from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Button:
    id: str
    title: str

    def to_dict(self) -> dict:
        return {"type": "reply", "reply": {"id": self.id, "title": self.title}}


@dataclass(frozen=True, slots=True)
class SectionRow:
    id: str
    title: str
    description: str | None = None

    def to_dict(self) -> dict:
        d = {"id": self.id, "title": self.title}
        if self.description:
            d["description"] = self.description
        return d


@dataclass(frozen=True, slots=True)
class Section:
    """https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#section-object"""
    title: str
    rows: list[SectionRow]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "rows": [row.to_dict() for row in self.rows]
        }


@dataclass(frozen=True, slots=True)
class SectionList:
    """https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#section-object"""
    button: str
    sections: list[Section]

    def to_dict(self) -> dict:
        return {
            "button": self.button,
            "sections": [section.to_dict() for section in self.sections]
        }
