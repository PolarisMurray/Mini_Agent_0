---
name: user-facts
description: Use when the user asks about themselves or anything known about them (name, preferences, background, past requests). Answer carefully, only from known facts.
---

# Answering questions about the user

A wrong "fact" about the user is worse than saying "I don't know".

## Steps
1. Look in the **Memory** section of the system prompt and in this conversation.
2. Answer only with what you found there, and say where it came from
   (e.g. "From a past session: ..." or "You said earlier: ...").
3. If the fact is missing, say so plainly and ask the user. Never guess.
4. If something is only implied, mark it as a guess ("It seems that ...") and ask to confirm.

## Rules
- Never invent names, dates, numbers, or preferences.
- Do not confuse the user with other people mentioned in the conversation.
- Keep the answer short and exact.

## More (load only when needed)
- Facts conflict or look outdated → `load_skill("user-facts", "reference/conflicts.md")`
