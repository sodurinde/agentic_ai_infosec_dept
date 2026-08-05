from beanie import Document


class Methodology(Document):
    name: str
    description: str
    min_score: int = 1
    max_score: int = 25

    class Settings:
        name = "methodologies"
