# Downstream LinkedIn Skill Handoff

Use installed LinkedIn skills as bounded renderers after the canonical content system routes the topic. Do not edit vendor/plugin skill files: updates may replace those edits.

## Precedence

Apply this order when instructions conflict:

1. explicit user constraints and approval state;
2. project positioning and account evidence;
3. verified claim/evidence boundaries;
4. canonical archetype, editorial treatment, format, and visual system;
5. downstream skill defaults.

Treat fixed length ranges, mandatory questions, forced vulnerability, generic voice quirks, posting times, reach multipliers, and “viral” formulas from downstream skills as optional hypotheses—not rules.

## Route envelope

Pass this packet in the downstream invocation. Keep distinct meanings: `content_theme` is the topical umbrella, `archetype` controls reasoning, `editorial_treatment` controls prose, and `visual_treatment` controls the asset.

```yaml
linkedin_route_v1:
  mode: plan | draft | audit | rewrite | extract | repurpose
  content_theme: "
  audience: "
  ai_product_connection: "
  engineering_question: "
  pillar: "
  primary_goal: saves | comments | reposts | likes | conversation

  evidence:
    status: PASS | QUALIFY | HOLD | REMOVE
    allowed_claims: []
    proof_or_sources: []
    required_limitations: []
    prohibited_or_unverified_claims: []

  content_design:
    archetype: "
    editorial_treatment: "
    information_shape: result | sequence | branching_choice | live_behavior | argument
    native_format: text | single_image | carousel | native_video | poll
    format_locked: true
    hook_seed: "
    cta: "                    # none is valid
    cta_locked: true

  visual_design:
    asset_required: false
    evidence_object: "
    visual_treatment: "
    brand_system: canonical_visual_brand_system
    generation_allowed: false

  voice:
    source: demonstrated_samples | approved_profile | generic_fallback
    must: []
    avoid: []
    named_creator_imitation: forbidden

  controls:
    edit_permission: no_edit | audit_only | rewrite
    add_new_facts: false
    publish_allowed: false
    locked_fields:
      - audience
      - evidence
      - archetype
      - editorial_treatment
      - native_format
      - visual_design
      - primary_goal
      - cta
```

Tell the downstream skill that locked fields cannot be replaced. If it cannot comply, it must return `constraint_conflict` rather than silently substitute a claim, archetype, format, theme, CTA, or asset.

## Skill boundaries

| Downstream skill | Allowed responsibility | Locked upstream |
|---|---|---|
| Content planner | Place routed cards into dates; suggest timing as a hypothesis | Pillars, per-post route, evidence state, goal |
| Interviewer | Elicit missing firsthand detail and proof | Positioning, no-invention rule, approval state |
| Post writer | Render one routed card; suggest compatible openings | Claims, format, CTA permission, voice, asset decision |
| Humanizer | Audit by default; rewrite only with permission | Meaning, facts, limitations, demonstrated voice |
| Hook extractor | Extract reusable mechanics and optional hook seeds | No copied wording, persona, catchphrase, or signature structure |
| Repurposer | Preserve the source spine and rebuild for the requested use | Source facts, evidence gate, destination route, approval state |

Re-run the format/theme gate when repurposing because a source format does not automatically fit the destination. Keep publication as a separate explicit approval step.
