from typing import List
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
import re

# Define LLM
llm = ChatOpenAI(base_url="http://127.0.0.1:5000/v1", api_key="not-needed", temperature=0, max_tokens=4000)

# Map
map_template = """Here is an excerpt from a given privacy policy: \n\n{docs}
Based on this list, please identify the scopes of information that may be collected
assuming the privacy policy is accepted.
"""
map_prompt = PromptTemplate.from_template(map_template)
map_chain = LLMChain(llm=llm, prompt=map_prompt)

# Reduce
reduce_template = """The following is a list of scopes: \n\n{docs}
Take these and distill it into a final, consolidated summary of the scopes."""
reduce_prompt = PromptTemplate.from_template(reduce_template)

reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)

# Combination Chain
combination_documents_chain = StuffDocumentsChain(
    llm_chain=reduce_chain, document_variable_name="docs"
)

# Combines and iteratively reduces the mapped documents
reduce_documents_chain = ReduceDocumentsChain(
    # This is final chain that is called.
    combine_documents_chain=combination_documents_chain,
    # If documents exceed context for `StuffDocumentsChain`
    collapse_documents_chain=combination_documents_chain,
    # The maximum number of tokens to group documents into.
    token_max=4000,
)

# Result Chain
summarizer_chain = MapReduceDocumentsChain(
    # Map chain
    llm_chain=map_chain,
    # Reduce chain
    reduce_documents_chain=reduce_documents_chain,
    # The variable name in the llm_chain to put the documents in
    document_variable_name="docs",
    # Return the results of the map steps in the output
    return_intermediate_steps=False,
)

# Splitter Tool

text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=3000, chunk_overlap=100
)


# Final Scope Aggregator
response_schemas = [
    ResponseSchema(name="scopes", description="A JSON list of 20 unique items or less composed of the categories of information that may be collected assuming the privacy policy is accepted."),
]

parser = StructuredOutputParser.from_response_schemas(response_schemas)

prompt = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of scopes from a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return a formatted summary of the privacy policy.""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
    validate_template=False
)

final_scope_chain = LLMChain(prompt=prompt,llm=llm,output_parser=parser)


# Final Scoring Chain
response_schemas2 = [
    ResponseSchema(name="score", description="An integer ranging from 0 to 100 inclusive that represents that scores the privacy and user friendliness of a privacy policy."),
]

parser2 = StructuredOutputParser.from_response_schemas(response_schemas2)

prompt2 = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of scopes from a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return a score representing the privacy friendliness of this privacy policy.""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser2.get_format_instructions()},
    validate_template=False
)

final_score_chain = LLMChain(prompt=prompt2,llm=llm,output_parser=parser2)

# Final Color Chain
response_schemas3 = [
    ResponseSchema(name="color", description="A hexadecimal color."),
]

parser3 = StructuredOutputParser.from_response_schemas(response_schemas3)

prompt3 = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return a color associated with the branding of the entity who owns this privacy policy.""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser3.get_format_instructions()},
    validate_template=False
)

final_color_chain = LLMChain(prompt=prompt3,llm=llm,output_parser=parser3)