

# imports
import streamlit as st
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Token, Span
from spacy import displacy
from spacy.pipeline import EntityRuler

from spacy.kb import KnowledgeBase
from py2neo import Graph,Subgraph,Node,Relationship,cypher,data
import pandas
from pandas import DataFrame
import numpy as np

# Graph load
graph = Graph("bolt://localhost:7687", user="neo4j", password="graph")

# Model load, NLP object init, vocab init
nlp = spacy.load("en_core_web_sm")
vocab = nlp.vocab

# Phrase matcher init
matcher = PhraseMatcher(nlp.vocab,attr="LOWER")


from spacy.pipeline import EntityRuler

# entity ruler creation
nlp = spacy.load("en_core_web_sm")
ruler = EntityRuler(nlp)

# match all classes
cursor = graph.run("match (class:Class) return class.name ")
df = DataFrame(cursor)

# creates a list of class nodes
classList = list(df[0])
patterns = []

# Creating a list of Tokens
for tokenClass in classList:
    cursor = graph.run("match (t:Token)-[:INSTANCE_OF]->(c:Class {name:'"+tokenClass+"'}) return t.name")
    df = DataFrame(cursor)
    tokenList = list(df[0])
    tokenList = [t.lower() for t in tokenList]

    patterns.append({"label":tokenClass,"pattern":[{"LOWER":{"IN":tokenList}}]})
ruler.add_patterns(patterns)
nlp.add_pipe(ruler)

# entity finder function
def entFinder(doc, entity):
    root1 = entity.root
    
    deps = dict()
    deps.update({root1.dep_:root1})
    
    for root2 in doc:
        deps.update({root2.dep_:root2})
        
    nsubj = deps.get("nsubj")
    dobj = deps.get("dobj")
    root = deps.get("ROOT")
        
    if(nsubj != None and dobj != None and root != None):

        cursor = graph.run("match(s:Class {name:'"+entity.label_+
                  "'})<-[r:"+str.upper(root.lemma_).replace(" ","_")+
                  "]->(e) return e.name")

        if(cursor.next!=None):
            df = DataFrame(cursor)
            #st.write(f"{entity.text:<10}{entity.label_:<10}")
            result = dict()
            st.write(dobj.text,":",df.iloc[0,0])



st.title("Entity Finder")

HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; 
                margin-bottom: 2.5rem">{}</div>"""

# text input
phrase = st.text_area("Enter your sentence...")
if st.button("Find Entities"):
	hush = dict()
	doc = nlp(phrase)
	st.subheader("Known Entities in the text:")

	#matcher(doc)
	html = displacy.render(doc, style="ent")

	# Newlines seem to mess with the rendering
	html = html.replace("\n", " ")
	st.write(HTML_WRAPPER.format(html), unsafe_allow_html=True)


	st.subheader("New entities found:")
	entFinder(doc,doc.ents[0])

	st.subheader("Update Matcher data?")
	st.checkbox("Update Matcher")


st.header("Matcher DataFrame")
if st.button("Show Recognized Input"):
	st.subheader("Valid relations")
	st.dataframe(DataFrame(graph.run("match (n:Class)-[r]->(m:Class) return n.name as starter, r.name as relation, m.name as ender")))
	st.subheader("Valid tokens")
	st.dataframe(DataFrame(graph.run("match (n:Token) return n.name,n.type")))