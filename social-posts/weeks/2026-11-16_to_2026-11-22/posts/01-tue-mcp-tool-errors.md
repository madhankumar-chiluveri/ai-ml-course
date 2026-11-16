---
post_id: LI-022
status: scheduled
scheduled_at: 2026-11-17T16:00:00+05:30
schedule_note: Buffer read-back verified automatic publishing on 17 November; LinkedIn 16:00 and Instagram 19:00 IST.
timezone: Asia/Kolkata
pillar: authority
format: document
instagram_format: carousel
visual_treatment: image-generated character scenes
visual_rationale: A delivered envelope with a warning makes the distinction visible.
primary_goal: technical-comments
instagram_primary_goal: saves
audience: full-stack engineers moving into AI product engineering
course_source: ../../../../course-path/phase-0-engineering-foundations/07_http_fundamentals.md
asset: ../assets/LI-022-mcp-tool-errors/LI-022-mcp-tool-errors.pdf
asset_source: ../assets/LI-022-mcp-tool-errors/source/prompts.md
buffer_linkedin_post_id: 6afb1d986b7e529a1fdf2c80
buffer_instagram_post_id: 6afb1da1da3ceb8b6ea0345b
media_commit: 42495e0fc63f503d2995fec6136dce6964170c1d
published_url:
instagram_published_url:
---

# Did the MCP tool succeed?

An MCP tool result may carry `isError: true`; an ordinary result object therefore does not alone establish that the operation succeeded. A protocol error is a separate outcome. Even when no tool error is reported, validate the expected business result. This is a documented mechanism, not a production incident or a measured experiment.

- **LinkedIn document:** [Five-page PDF](../assets/LI-022-mcp-tool-errors/LI-022-mcp-tool-errors.pdf).
- **Instagram carousel:** [Five ordered PNGs](../assets/LI-022-mcp-tool-errors/LI-022-instagram-carousel.zip).
- **Source:** [Generation and packaging notes](../assets/LI-022-mcp-tool-errors/source/prompts.md).
- **Scheduling evidence:** Buffer read-back confirmed both captions, automatic publishing, LinkedIn PDF and cover, and the five Instagram images in order. Public GitHub media URLs are pinned to the media commit above; anonymous downloads matched the local PDF and PNGs. They have no configured expiry.
- **Primary sources:** [MCP TypeScript SDK: tool and protocol errors](https://ts.sdk.modelcontextprotocol.io/v2/servers/errors) and [MCP C# SDK: error handling](https://csharp.sdk.modelcontextprotocol.io/v1/concepts/tools/tools.html).
- **Alt text:** 1. An engineer checks whether a delivered tool result means success. 2. A result envelope arrives with a warning inside, illustrating an MCP tool error. 3. A protocol error and a tool error follow distinct paths. 4. Check the error flag, message, and expected output before reporting an outcome. 5. Ask whether the request succeeded, whether the tool reported an error, and whether the output meets the task.

## LinkedIn

### Final copy

𝐘𝐨𝐮𝐫 𝐌𝐂𝐏 𝐭𝐨𝐨𝐥 𝐜𝐚𝐥𝐥 𝐫𝐞𝐭𝐮𝐫𝐧𝐞𝐝. 𝐃𝐢𝐝 𝐭𝐡𝐞 𝐭𝐨𝐨𝐥 𝐚𝐜𝐭𝐮𝐚𝐥𝐥𝐲 𝐬𝐮𝐜𝐜𝐞𝐞𝐝?

An agent asks a tool to retrieve a record. A result comes back.

That tells you the caller received a result. It does not, by itself, tell you the task succeeded.

In MCP, a tool can return a result with isError: true. The result may contain a message explaining the tool failure.

That differs from a protocol error, where the request itself could not be handled.

Before your agent tells the user “done”:

• Handle protocol errors.
• Check whether the tool result reports an error.
• Read the tool's message and validate the expected output.
• Report the actual outcome.

Even a result without a reported tool error is not proof that the business task was completed correctly. Check the outcome your application requires.

The carousel illustrates the distinction using the MCP SDK documentation. It is not a production incident.

How does your agent distinguish a delivered result from a completed task?

#AIEngineering #MCP #SoftwareEngineering

## Instagram

### Caption

Your AI agent received a tool result. That does not automatically mean the tool succeeded.

An MCP result can report isError: true. A protocol error is a separate case.

Check the error, read the message, and validate the output before the agent reports “done.”

Swipe through the distinction and save the checklist for your next agent integration.

#MCP #AIEngineering #AgenticAI
