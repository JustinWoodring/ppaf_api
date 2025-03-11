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
# regular Map
map_template = """Here is an excerpt from a given privacy policy: \n\n{docs}
Based on this list, please identify the scopes of information that may be collected
assuming the privacy policy is accepted.
"""
map_prompt = PromptTemplate.from_template(map_template)
map_chain = LLMChain(llm=llm, prompt=map_prompt)

# Data shared Map
data_shared_map_template = """Here is an excerpt from a given privacy policy: \n\n{docs}
Based on this text, please identify the types of data that may be shared with third parties or external entities.
"""
data_shared_map_prompt = PromptTemplate.from_template(data_shared_map_template)
shared_map_chain = LLMChain(llm=llm, prompt=data_shared_map_prompt)

# Data colected Map
data_collected_map_template = """Here is an excerpt from a given privacy policy: \n\n{docs}
Based on this list, please identify the types of data that will be collected by the organization.
"""
data_collected_map_prompt = PromptTemplate.from_template(data_collected_map_template)
collected_map_chain = LLMChain(llm=llm, prompt=data_collected_map_prompt)

# security practices Map
security_map_template = """Here is an excerpt from a given privacy policy: \n\n{docs}
Based on this list, please list the security practices or measures in place to protect the user's data.
"""
security_map_prompt = PromptTemplate.from_template(security_map_template)
security_map_chain = LLMChain(llm=llm, prompt=security_map_prompt)

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

# Result Chains

#data shared
shared_map_chain = MapReduceDocumentsChain(
    # Map chain
    llm_chain=shared_map_chain,
    # Reduce chain
    reduce_documents_chain=reduce_documents_chain,
    # The variable name in the llm_chain to put the documents in
    document_variable_name="docs",
    # Return the results of the map steps in the output
    return_intermediate_steps=False,
)

#data collected
collected_map_chain = MapReduceDocumentsChain(
    # Map chain
    llm_chain=collected_map_chain,
    # Reduce chain
    reduce_documents_chain=reduce_documents_chain,
    # The variable name in the llm_chain to put the documents in
    document_variable_name="docs",
    # Return the results of the map steps in the output
    return_intermediate_steps=False,
)

#security practices
security_map_chain = MapReduceDocumentsChain(
    # Map chain
    llm_chain=security_map_chain,
    # Reduce chain
    reduce_documents_chain=reduce_documents_chain,
    # The variable name in the llm_chain to put the documents in
    document_variable_name="docs",
    # Return the results of the map steps in the output
    return_intermediate_steps=False,
)

#regular Map
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

#Final data shared chain
response_schemas2 = [
    ResponseSchema(name="shared", description="Types of user data that may be shared with third parties or external entities according to the privacy policy." )
]

parser2 = StructuredOutputParser.from_response_schemas(response_schemas2)

prompt2 = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of scopes from a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return what user or collected data may be shared with third parties or external entities according to the policy.""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser2.get_format_instructions()},
    validate_template=False
)

final_shared_chain = LLMChain(prompt=prompt2,llm=llm,output_parser=parser2)

#Final data collected chain
response_schemas3 = [
    ResponseSchema(name="collected", description="All data that will be collected from the user by the organization per the privacy policy." )
]

parser3 = StructuredOutputParser.from_response_schemas(response_schemas3)

prompt3 = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of scopes from a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return the types of data that may be collected by the organization per the privacy policy""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser3.get_format_instructions()},
    validate_template=False
)

final_collected_chain = LLMChain(prompt=prompt3,llm=llm,output_parser=parser3)

#Final security practices chain
response_schemas4 = [
    ResponseSchema(name="security", description="Security methods in place to protect the user's data per the privacy policy, including any user rights such as requesting data deletion, opting out, or controlling access to their personal information." )
]

parser4 = StructuredOutputParser.from_response_schemas(response_schemas4)

prompt4 = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of scopes from a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return all the specific security measures and rights available to users that are designed to protect their personal data.
""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser4.get_format_instructions()},
    validate_template=False
)

final_security_chain = LLMChain(prompt=prompt4,llm=llm,output_parser=parser4)

# Final Scoring Chain
response_schemas5 = [
    ResponseSchema(name="score", description="An integer ranging from 0 to 100 inclusive that represents that scores the privacy and user friendliness of a privacy policy."),
]

parser5 = StructuredOutputParser.from_response_schemas(response_schemas5)

prompt5 = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of scopes from a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return a score representing the privacy friendliness of this privacy policy.""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser5.get_format_instructions()},
    validate_template=False
)

final_score_chain = LLMChain(prompt=prompt5,llm=llm,output_parser=parser5)

# Final Color Chain
response_schemas6 = [
    ResponseSchema(name="color", description="A hexadecimal color."),
]

parser6 = StructuredOutputParser.from_response_schemas(response_schemas6)

prompt6 = PromptTemplate(
    template="""You are a helpful, honest assistant. 
    
Here is a summary of a privacy policy:\n\n{summary}\n\nPlease strictly adhere to the following format instructions. {format_instructions}. 

Please return a color associated with the branding of the entity who owns this privacy policy.""",
    input_variables=["summary"],
    partial_variables={"format_instructions": parser6.get_format_instructions()},
    validate_template=False
)

final_color_chain = LLMChain(prompt=prompt6,llm=llm,output_parser=parser6)