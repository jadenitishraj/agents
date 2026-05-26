"""HyDE query expansion helpers."""

from __future__ import annotations

from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.query_engine import TransformQueryEngine

from .llm import get_llama_llm


def build_query_bundle(question: str):
    transform = HyDEQueryTransform(llm=get_llama_llm(), include_original=True)
    return transform.run(question)


def build_transform_engine(vector_index):
    transform = HyDEQueryTransform(llm=get_llama_llm(), include_original=True)
    engine = vector_index.as_query_engine(similarity_top_k=4)
    return TransformQueryEngine(engine, transform)
