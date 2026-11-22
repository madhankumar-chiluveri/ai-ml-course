---
post_id: LI-025
status: review
scheduled_at: 2026-11-23T22:00:00+05:30
instagram_scheduled_at: 2026-11-23T19:00:00+05:30
timezone: Asia/Kolkata
pillar: authority
format: document
instagram_format: carousel
visual_treatment: image-generated editorial illustrations
visual_rationale: Five illustrated pages show how AWS established expected behavior, tested one queue message, and reported the result. The final page works through a reader example.
primary_goal: comments
instagram_primary_goal: saves
audience: Full-stack engineers using coding agents
proof_type: source_analysis
public_credit: madvibe.ai
asset: ../assets/LI-025-aws-emulator-fidelity/LI-025-aws-emulator-fidelity.pdf
instagram_asset: ../assets/LI-025-aws-emulator-fidelity/LI-025-instagram-carousel.zip
asset_source: ../assets/LI-025-aws-emulator-fidelity/source/prompts.md
published_url:
instagram_published_url:
---

# How AWS checked its AI-written emulator

- [LinkedIn document](../assets/LI-025-aws-emulator-fidelity/LI-025-aws-emulator-fidelity.pdf)
- [Instagram carousel, five ordered PNGs](../assets/LI-025-aws-emulator-fidelity/LI-025-instagram-carousel.zip)
- [Generation prompts and native sources](../assets/LI-025-aws-emulator-fidelity/source/prompts.md)

### Page alt text

1. A cloud labeled Real AWS points toward a laptop labeled Local emulator. AWS agents wrote an emulator that lets developers test AWS API calls locally.
2. AWS runs a scenario against the real cloud, records the expected behavior, and repeats the same check on the emulator.
3. A worker receives one SQS message and leaves it undeleted. An immediate second read returns nothing. After the test's two-second visibility timeout, the same message ID returns.
4. AWS Emulator release v1.0.322 records a pass for the SQS visibility timeout check. The result covers this single behavior.
5. An example test feeds Order 42 to a worker twice and expects one order record. Run this same check on the original and replacement workers.

## Evidence

- [AWS engineering write-up](https://www.aboutamazon.com/news/aws/how-autonomous-ai-agents-built-aws-emulator), 11 November 2026. AWS engineer Matthew Goldberg describes validating checks against real AWS and replaying them against the emulator.
- [AWS SQS test source](https://github.com/aws/aws-emulator-evaluation-suite/blob/4df2823bafface2ada35f482c07ff6668cc078e1/behavioral/sqs/check_visibility_timeout_natural_expiry.py) and [AWS Emulator v1.0.322 release](https://github.com/aws/aws-emulator/releases/tag/v1.0.322). On 22 November 2026, the downloaded release score marked the matching unit, sqs.visibility-timeout-natural-expiry, as pass. The two-second timeout is the test configuration. The diagram depicts the test and the published result.
- [Hands-on LinkedIn post](https://pt.linkedin.com/posts/guilherme-benfica_awsgoldenjacket-goldenjacketbrazil-activity-7528226552715763713-w4h-) and [19 November AWS team AMA](https://www.reddit.com/r/aws/comments/1y08smf/were_the_team_behind_aws_emulator_a_local_aws/) informed topic selection.

## LinkedIn

### Final copy

𝐇𝐨𝐰 𝐝𝐢𝐝 𝐀𝐖𝐒 𝐜𝐡𝐞𝐜𝐤 𝐭𝐡𝐞 𝐞𝐦𝐮𝐥𝐚𝐭𝐨𝐫 𝐢𝐭𝐬 𝐀𝐈 𝐚𝐠𝐞𝐧𝐭𝐬 𝐰𝐫𝐨𝐭𝐞?

The emulator lets developers test AWS integrations on their own machines. AWS checked its behavior by running the tests against the real cloud first.

Take one check for Amazon SQS, the service that queues messages for workers.

A worker receives a message and leaves it undeleted. A second read immediately finds nothing. Once the visibility timeout expires, the test receives the same message ID again. That lets a worker retry the job if the first worker crashes.

AWS replayed that check against the emulator. Its v1.0.322 release report marks the check as passed. AWS publishes the test suite and scores so you can look up the specific behavior your app depends on.

The last slide turns this into a test you can use. Feed the same order to a worker twice and check that it creates one record. Run the check on both versions when you replace the worker.

What behavior would you check first in a system you maintain?

AWS release report
https://github.com/aws/aws-emulator/releases/tag/v1.0.322

#AIEngineering #AWS

## Instagram

### Caption

How AWS checked code written by AI agents.

One SQS message goes out. A second read returns nothing. After the visibility timeout, the same message ID comes back.

AWS checked that behavior on the real cloud, then replayed the test on AWS Emulator. Its v1.0.322 report records a pass for that check.

Save this for your next rewrite. The last slide shows how to check that processing the same order twice produces one order record.

#AWSEmulator #AICoding #SoftwareTesting
