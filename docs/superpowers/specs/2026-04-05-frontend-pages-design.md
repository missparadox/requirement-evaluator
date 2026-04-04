# Frontend Pages Design

## Scope

This document finalizes the approved visual and structural direction for the phase 1 frontend pages of the requirements evaluator service.

In scope:

- upload page
- evaluation detail page
- shared page-head system across both pages
- copy tone, layout hierarchy, and module boundaries

Out of scope:

- API wiring details
- polling and state update interaction behavior
- backend behavior
- implementation task breakdown

## Shared Design System

### Product Tone

Both pages must feel like a commercial product rather than an internal workflow tool.

The approved tone is:

- formal
- restrained
- premium
- trustworthy
- structured

Avoid:

- conversational or tutorial-like phrasing
- prototype-style layouts
- playful or overly bright presentation
- inconsistent page header treatment between routes

### Shared Header System

The upload page and detail page must use the same header system.

Required rules:

- small English overline above the title
- centered Chinese main title
- same Chinese title font family on both pages
- same Chinese title size tier on both pages
- same English overline styling on both pages
- same vertical rhythm from overline to title to following content

This is a hard consistency requirement. The two pages may differ in the body layout below the header, but the top title system must remain visually unified.

### Shared Visual Direction

The approved palette is a restrained warm neutral system:

- warm ivory backgrounds
- soft brown-gold accent tones
- dark brown typography
- low-contrast premium card surfaces

Avoid loud orange accents or utility-dashboard colors.

Typography should feel editorial and polished:

- serif/display treatment for the Chinese main title
- clean sans-serif for labels, body copy, controls, and metadata

## Upload Page

### Page Positioning

The upload page is a premium platform landing entry, not a small utility form.

Its purpose is to:

- establish product positioning
- explain the evaluation flow at a high level
- provide a clear single upload entry point

### Header

Primary title:

`需求评估平台`

Rules:

- centered
- visually dominant
- no competing Chinese subtitle above it

Supporting copy should emphasize:

- unified quality assessment entry
- structured analysis
- standardized report output
- risk identification and maturity improvement

### Body Structure

The page hierarchy is:

1. English overline
2. centered Chinese title
3. centered supporting copy
4. three-step process section
5. upload action container

### Process Section

The upload page includes three horizontally aligned stage cards:

- 阶段 01: 提交评估文件
- 阶段 02: 执行自动分析
- 阶段 03: 获取评估结果

These cards exist to explain the platform flow, not to teach the user through casual instructions.

### Upload Action Module

The upload area is a composed action module with two different action weights:

- secondary action: `选择文件`
- primary action: `开始评估`

Interaction rules:

- `选择文件` only selects a file
- `开始评估` is the single primary submission action
- these two controls must not visually compete as equal primary buttons

Visual rules:

- include a section label such as `评估文件上传`
- show a passive file display surface
- place the file picker as a lighter secondary control
- keep the submit button visually strongest
- include a short formal note about supported file formats and automatic processing

### Layout Proportion

The main upload panel should occupy a generous portion of the screen and feel balanced with the detail page card proportions. It should not shrink into a small centered card.

## Evaluation Detail Page

### Page Positioning

The detail page is a formal result page with decision-oriented summary structure.

It is not a long-form report reader and not a dense operational dashboard.

Its purpose is to:

- identify the task clearly
- surface the evaluation outcome quickly
- present the most important decision signals
- provide access to the formal downloadable report

### Header

Primary title:

`需求评估结果`

Rules:

- centered
- same title system as the upload page
- no left-aligned page title block

### Section Structure

The page body is divided into two major sections:

- `任务信息`
- `评估结论`

Both section titles must use the same centered label treatment with symmetrical divider lines on both sides.

These sections should sit lower than the page title block so the header and body feel clearly separated.

### Task Information Section

`任务信息` is a metadata section rather than inline text.

It should be displayed as three separate cards:

- 评估编号
- 文件名称
- 任务状态

Rules:

- cards appear in a three-column row on desktop
- each card is centered internally
- metadata should not be collapsed into one text line

### Evaluation Conclusion Section

The `评估结论` section contains:

- a primary conclusion card
- supporting score/state cards
- three secondary summary cards
- a final summary block

#### Primary Conclusion Card

This is the visual anchor of the detail page.

It contains:

- a small overline label
- the main conclusion statement
- a short supporting paragraph

The report download action belongs inside this conclusion module, not in the page header.

Approved placement:

- the `下载评估报告` button sits in the top-right area inside the primary conclusion card

This avoids creating a disconnected action row between the section divider and the conclusion content.

#### Supporting Score and State Cards

To the side of the primary conclusion card, show:

- `总体评分`
- `建议状态`

Rules:

- stacked vertically
- aligned with the height rhythm of the conclusion card
- centered internally

#### Secondary Summary Cards

Below the main conclusion row, show three evenly aligned cards:

- `核心风险`
- `优先动作`
- `评估说明`

Rules:

- equal width
- equal visual weight
- aligned heights on desktop

#### Final Summary Block

The last block is a centered `摘要结论` card that gives a compact closing statement in more formal prose.

### Layout Proportion

The overall detail page card should be proportionally aligned with the upload page. It should feel like the same product family rather than a narrower or denser internal console.

## Responsive Behavior

On narrow screens:

- the title system remains centered
- section divider titles remain centered
- metadata cards may stack vertically
- the main conclusion row may collapse into a single column
- summary cards may stack vertically
- the download button must remain easy to reach and visually attached to the conclusion module

## Copy Guidance

Both pages should use product-grade Chinese copy.

Preferred characteristics:

- businesslike
- precise
- calm
- governance-oriented

Avoid:

- chatty instructions
- overly operational microcopy
- exaggerated marketing language
- inconsistent terminology across pages

## Final Approved Decisions

- both pages use the same centered title system
- upload page title is `需求评估平台`
- detail page title is `需求评估结果`
- upload page is a premium landing-style entry page
- detail page is a decision-oriented result page
- `任务信息` and `评估结论` both use centered divider titles
- detail page metadata is shown as three separate cards
- report download action is embedded in the primary conclusion card
- both pages share the same restrained premium visual language
