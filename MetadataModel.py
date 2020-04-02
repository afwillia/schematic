import pandas as pd
import networkx as nx
import json
import re
from jsonschema import validate, ValidationError


# allows specifying explicit variable types
from typing import Any, Dict, Optional, Text

# handle schema logic; to be refactored as SchemaExplorer matures into a package
# as collaboration with Biothings progresses
from schema_explorer import SchemaExplorer
from ManifestGenerator import ManifestGenerator
from schema_generator import get_JSONSchema_requirements, get_component_requirements, get_descendants_by_edge_type

class MetadataModel(object):

     """Metadata model wrapper around schema.org specification graph.
     Provides basic utilities to 

     1) manipulate the metadata model;
     2) generate metadata model views:
        - generate manifest view of the metadata metadata model
        - generate validation schemas view of the metadata model;
     """

     def __init__(self,
                 inputMModelLocation: str,
                 inputMModelLocationType: str,
                 ) -> None:

        """ Instantiates MetadataModel object

        Args: 
          se: a SchemaExplorer instance 
          inputMModelLocation:  local path, uri, synapse entity id; (e.g. gs://, syn123, /User/x/…); present location
        """
        
        self.se = SchemaExplorer()

        self.inputMModelLocationType = inputMModelLocationType 
        self.inputMModelLocation = inputMModelLocation
        
        self.loadMModel()



     # setting mutators/accessors methods explicitly

     @property
     def inputMModelLocation(self) -> str:
         """Gets or sets the inputMModelLocation path"""
         return self.__inputMModelLocation

     @inputMModelLocation.setter
     def inputMModelLocation(self, inputMModelLocation) -> None:
         self.__inputMModelLocation = inputMModelLocation 


     @property
     def inputMModelLocationType(self) -> str:
         """Gets or sets the inputMModelLocationType"""
         return self.__inputMModelLocationType

     @inputMModelLocationType.setter
     def inputMModelLocationType(self, inputMModelLocationType) -> None:
         self.__inputMModelLocationType = inputMModelLocationType


     @property
     def se(self) -> SchemaExplorer:
         """Gets or sets the SchemaExplorer instance"""
         return self.__se

    
     @se.setter
     def se(self, se: SchemaExplorer) -> None:
         self.__se = se
    

     # business logic: expose metadata model "views" depending on "controller" logic
     # (somewhat analogous to Model View Controller pattern for GUI/web applications)
     # i.e. jsonschemas, annotation manifests, metadata/annotation dictionary web explorer
     # are all "views" of the metadata model.
     # The "business logic" in this MetadataModel class provides functions exposing relevant parts
     # of the metadata model needed so that these views can be generated by user facing components;
     # controller components are (loosely speaking) responsible for handling the interaction between views and the model
     # some of these components right now reside in the Bundle class

     def loadMModel(self) -> None:
         """ load Schema; handles schema file input and sets mmodel
         """

         self.se.load_schema(self.inputMModelLocation)


     def getModelSubgraph(self, rootNode: str, 
                         subgraphType: str) -> nx.DiGraph:
         """ get a schema subgraph from rootNode descendants on edges/node properties of type subgraphType
         Args:
          rootNode: a schema node label (i.e. term)
          subgraphType: the kind of subgraph to traverse (i.e. based on node properties or edge labels)
        
         Returns: a directed graph (networkx DiGraph) subgraph of the metadata model w/ vertex set root node descendants

         Raises: 
             ValueError: rootNode not found in metadata model.
         """
         pass

     def getOrderedModelNodes(self, rootNode: str, relationshipType: str) -> list:
        """ get a list of model objects ordered by their topological sort rank in a model subgraph on edges of a given relationship type.

        Args:
          rootNode: a schema object/node label (i.e. term); all returned nodes will be this node's descendants
          relationshipType: edge label type of the schema subgraph (e.g. requiresDependency)
        Returns: an ordered list of objects 
         Raises: TODO 
             ValueError: rootNode not found in metadata model.
        """

        ordered_nodes = get_descendants_by_edge_type(self.se.schema_nx, rootNode, relationshipType, connected = True, ordered = True)

        ordered_nodes.reverse()

        return ordered_nodes
         

     def getModelManifest(self, title, rootNode:str, filenames:list = None) -> str: 

         """ get annotations manifest dataframe 
         Args:
          rootNode: a schema node label (i.e. term)
        
         Returns: a manifest URI (assume Google doc for now) 
         Raises: 
            ValueError: rootNode not found in metadata model.
         """

         additionalMetadata = {}
         if filenames:
             additionalMetadata["Filename"] = filenames

         mg = ManifestGenerator(title, self.se, rootNode,  additionalMetadata)

         return mg.get_manifest()


     def get_component_requirements(self, source_component: str) -> list:

        """ Given a source model component (see https://w3id.org/biolink/vocab/category for definnition of component), return all components required by it. Useful to construct requirement dependencies not only between specific attributes but also between categories/components of attributes; can be utilized to track metadata copletion progress across multiple categories of attributes.
        Args: 
            source_component: an attribute label indicating the source component

        Returns: a list of required components associated with the source component
        """
        
        # get metadata model schema graph
        mm_graph = self.se.get_nx_schema()

        # get required components for the input component
        req_components = get_component_requirements(mm_graph, source_component) 

        return req_components


    # TODO: abstract validation in its own module

     def validateModelManifest(self, manifestPath:str, rootNode:str, jsonSchema:str = None) -> list:
         
         """ check if provided annotations manifest dataframe 
         satisfied all model requirements
         Args:
          rootNode: a schema node label (i.e. term)
          manifestPath: a path to the manifest csv file containing annotations
        
         Returns: a validation status message; if there is an error the message 
         contains the manifest annotation record (i.e. row) that is invalid, along 
         with the validation error associated with this record
         Raises: TODO 
            ValueError: rootNode not found in metadata model.
         """

         # get validation schema for a given node in the data model
         if not jsonSchema:
             jsonSchema = get_JSONSchema_requirements(self.se, rootNode, rootNode + "_validation")
         
         # get annotations from manifest (array of json annotations corresponding to manifest rows)

         manifest = pd.read_csv(manifestPath).fillna("")
         manifest_trimmed = manifest.apply(lambda x: x.str.strip() if x.dtype == "object" else x)###remove whitespaces from manifest
         annotations = json.loads(manifest_trimmed.to_json(orient='records'))

         errorPositions = []
         for i, annotation in enumerate(annotations):
             
             try:
                validate(instance = annotation, schema = jsonSchema)
             # this error parsing is too brittle; if something changes in the validator code outputting the validation error we'd have to change the logic; TODO: provide a more robust error parsing
             except ValidationError as e:
                listExp = re.compile('\[(.*?)\]')
                
                errorRow = i + 2 # row in the manifest where the error occurred

                # parse the validation error in a more human readable form
                errorMessage = "At row " + str(errorRow) + ": "
                
                errors = str(e).split("\n")
                
                stringExp = re.compile('\'(.*?)\'')

                # extract wrong value entered
                errorValue = stringExp.findall(errors[0])[0]

                errorMessage += errors[0]
                
                # extract allowed values, if any, for the term that was erroneously filled in
                allowedValues = listExp.findall(errorMessage)
                
                if allowedValues:
                    allowedValues = allowedValues[0].replace('\'', '').split(", ")
                
                errorDetail = errors[-2].replace("On instance", "At term")

                #extract the term(s) that had erroneously filled in values, if any
                errorTerms = listExp.findall(errorDetail)
                if errorTerms:
                    errorTerms = errorTerms[0].replace('\'','').split(", ")[0]

                errorMessage += "; " + errorDetail
                errorDetail = " value " + errors[-1].strip() + " is invalid;"
                errorMessage += errorDetail

                errorPositions.append((errorRow, errorTerms, errorValue, allowedValues))
         
         return errorPositions

     
     def populateModelManifest(self, title, manifestPath:str, rootNode:str) -> str:
         
         """ populate an existing annotations manifest based on a dataframe          
         
         Args:
          rootNode: a schema node label (i.e. term)
          manifestPath: a path to the manifest csv file containing annotations
        
         Returns: a link to the filled in model manifest (e.g. google sheet)

         Raises: TODO 
            ValueError: rootNode not found in metadata model.
         """
         #mg = ManifestGenerator(title, self.se, rootNode, {"Filename":[]})
         
         mg = ManifestGenerator(title, self.se, rootNode)
         emptyManifestURL = mg.get_manifest()

         return mg.populate_manifest_spreadsheet(manifestPath, emptyManifestURL)

