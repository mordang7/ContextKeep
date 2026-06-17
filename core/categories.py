"""Starter categories and migration categorization helpers."""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List, Mapping


STARTER_CATEGORIES = [
    {
        "name": "Projects",
        "description": "Active development projects, repositories, milestones, and project-specific context",
        "icon": "rocket",
    },
    {
        "name": "Hardware & Infrastructure",
        "description": "Device specs, inventory, network gear, homelab setup, NAS, servers",
        "icon": "monitor",
    },
    {
        "name": "Credentials & Access",
        "description": "API keys, passwords, SSH keys, tokens, login details, access configurations",
        "icon": "lock",
    },
    {
        "name": "People & Contacts",
        "description": "Contact information, relationships, team members, collaborators",
        "icon": "users",
    },
    {
        "name": "Workflows & Automation",
        "description": "Processes, procedures, scripts, agent directives, recurring tasks, how-tos",
        "icon": "gear",
    },
    {
        "name": "Content & Media",
        "description": "YouTube videos, blog posts, social media, scripts, thumbnails, media assets",
        "icon": "film",
    },
    {
        "name": "Configuration & Settings",
        "description": "Tool configs, environment settings, preferences, system setup, dotfiles",
        "icon": "wrench",
    },
    {
        "name": "Knowledge & Research",
        "description": "Notes, articles, references, learning resources, technical documentation",
        "icon": "book",
    },
    {
        "name": "Personal",
        "description": "Goals, preferences, personal information, reminders, lifestyle notes",
        "icon": "user",
    },
]


CATEGORY_KEYWORDS = {
    "Projects": [
        "project",
        "repo",
        "github",
        "build",
        "deploy",
        "deployment",
        "release",
        "version",
        "feature",
        "bug",
        "milestone",
        "development",
    ],
    "Hardware & Infrastructure": [
        "hardware",
        "cpu",
        "gpu",
        "ram",
        "ssd",
        "nvme",
        "nas",
        "server",
        "homelab",
        "network",
        "router",
        "switch",
        "device",
        "laptop",
        "desktop",
        "monitor",
        "spec",
    ],
    "Credentials & Access": [
        "password",
        "api_key",
        "api key",
        "token",
        "ssh",
        "credential",
        "login",
        "secret",
        "auth",
        "access",
    ],
    "People & Contacts": [
        "contact",
        "email",
        "phone",
        "person",
        "team",
        "member",
        "relationship",
    ],
    "Workflows & Automation": [
        "workflow",
        "script",
        "automation",
        "cron",
        "schedule",
        "process",
        "procedure",
        "template",
        "directive",
        "agent",
        "protocol",
    ],
    "Content & Media": [
        "video",
        "youtube",
        "thumbnail",
        "geekj",
        "channel",
        "episode",
        "recording",
        "stream",
        "content",
        "media",
        "blog",
        "post",
    ],
    "Configuration & Settings": [
        "config",
        "setting",
        "setup",
        "preference",
        "dotfile",
        "environment",
        "install",
        "path",
        "alias",
    ],
    "Knowledge & Research": [
        "research",
        "note",
        "article",
        "documentation",
        "docs",
        "guide",
        "tutorial",
        "reference",
        "learning",
        "study",
    ],
    "Personal": [
        "personal",
        "goal",
        "reminder",
        "preference",
        "birthday",
        "family",
        "hobby",
        "health",
        "lifestyle",
    ],
}


WORD_RE = re.compile(r"[\w+#.-]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Return lowercase tokens while keeping simple technical terms intact."""
    return [token.lower() for token in WORD_RE.findall(text or "")]


def categorize_memory(
    key: str,
    title: str,
    content: str,
    legacy_tags: Iterable[str] | None = None,
    minimum_score: int = 2,
) -> List[str]:
    """Choose starter categories for imported V1 memories.

    The heuristic is intentionally simple and transparent. It scores key, title,
    legacy tags, and content together, then returns every category above the
    threshold. Callers should create an Uncategorized bucket when this returns no
    results.
    """
    tags = list(legacy_tags or [])
    haystack = " ".join([key or "", title or "", " ".join(tags), content or ""]).lower()
    tokens = Counter(tokenize(haystack))
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            keyword_l = keyword.lower()
            if " " in keyword_l:
                score += haystack.count(keyword_l) * 2
            else:
                score += tokens.get(keyword_l, 0)
        if score >= minimum_score:
            scores[category] = score

    return [
        category
        for category, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ]


def category_names(categories: Iterable[Mapping[str, object]]) -> list[str]:
    return [str(category["name"]) for category in categories]

