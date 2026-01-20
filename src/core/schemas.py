"""Pydantic schemas for ConvFinQA data structures."""

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Financial document with text and table."""

    pre_text: str = Field(description="Text before the table")
    post_text: str = Field(description="Text after the table")
    table: dict[str, dict[str, float | str | int]] = Field(
        description="Table data as nested dict"
    )


class Dialogue(BaseModel):
    """Conversational dialogue about a document."""

    conv_questions: list[str] = Field(description="Questions in the conversation")
    conv_answers: list[str] = Field(description="Answers to each question")
    turn_program: list[str] = Field(description="DSL program for each turn")
    executed_answers: list[float | str] = Field(description="Gold execution results")
    qa_split: list[bool] = Field(description="Source of each question turn")


class Features(BaseModel):
    """Metadata features for a record."""

    num_dialogue_turns: int
    has_type2_question: bool
    has_duplicate_columns: bool
    has_non_numeric_values: bool


class ConvFinQARecord(BaseModel):
    """A single record from the ConvFinQA dataset."""

    id: str = Field(description="Record ID")
    doc: Document = Field(description="The financial document")
    dialogue: Dialogue = Field(description="The conversational dialogue")
    features: Features = Field(description="Record metadata")


class ConvFinQADataset(BaseModel):
    """The complete dataset structure."""

    train: list[ConvFinQARecord]
    dev: list[ConvFinQARecord]
