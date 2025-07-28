Research Agent RAG System Documentation
========================================

A multi-agent research system that combines RAG (Retrieval-Augmented Generation) 
with specialized AI agents to analyze academic papers and generate insights from 
multiple expert perspectives.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api
   examples
   contributing

Features
--------

* **Multi-Agent Analysis**: Specialized agents for different perspectives
* **Paper Retrieval**: Automatic paper fetching from arXiv
* **Vector Storage**: Semantic search using ChromaDB
* **Interactive Chat**: Conversational interface for paper discussions
* **Research Sessions**: Comprehensive workflow management

Quick Start
-----------

.. code-block:: bash

   # Complete setup
   make setup
   
   # Run demonstration
   make run-demo
   
   # Launch web interface
   make run-web

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`