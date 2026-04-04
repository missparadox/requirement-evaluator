# Upload Page Design

## Scope

This document finalizes the upload page visual and interaction direction for the requirements evaluator frontend.

In scope:

- upload page only
- first-screen layout and copy
- upload area interaction structure
- visual tone and brand direction

Out of scope:

- evaluation detail page redesign
- real API wiring details
- backend behavior changes

## Approved Direction

The upload page uses a centered, premium product landing layout rather than a small utility card.

The page should present the product as a formal platform, not an internal tool. The first screen must feel closer to a commercial SaaS entry page than to a temporary workflow shell.

## Content Hierarchy

The page hierarchy is:

1. small English brand line
2. single large centered Chinese title
3. centered supporting copy
4. three-step process summary
5. upload action container

### Title

The only primary title is:

`需求评估平台`

Rules:

- center aligned
- visually dominant
- significantly larger than any other text on the page
- no competing Chinese subtitle above it

The small English line may remain as a light brand marker, but it must not compete with the Chinese title.

### Supporting Copy

Supporting copy should sound formal, commercial, and professional.

Approved tone:

- platform-oriented
- quality-governance oriented
- delivery-readiness oriented
- restrained and credible

Avoid:

- conversational phrasing
- tutorial-like wording
- internal-tool tone
- overly casual action copy

The supporting copy should emphasize value such as:

- unified quality assessment entry
- structured analysis
- standardized report output
- risk identification
- deviation control
- requirement maturity improvement

## Layout

### Overall Structure

The page uses a large centered panel on top of a warm, restrained background.

The panel should:

- occupy a clearly larger proportion of the viewport than the current implementation
- feel balanced on desktop
- remain readable on mobile
- use generous padding and rounded corners

### Process Section

Below the main copy, show three horizontally aligned stages:

- 阶段 01: 提交评估文件
- 阶段 02: 执行自动分析
- 阶段 03: 获取评估结果

Each stage card should:

- use formal wording
- have equal visual weight
- reinforce the product flow without feeling instructional or playful

## Upload Action Area

The upload container is a combined action module with two levels of action:

- secondary action: `选择文件`
- primary action: `开始评估`

### Interaction Roles

`选择文件` is responsible for file picking only.

`开始评估` is the primary submission action.

These two actions must not look like competing primary buttons.

### Visual Rules

The upload area should contain:

- a section label such as `评估文件上传`
- a passive file display field
- a secondary file-picker button
- a high-emphasis primary submit button
- a short formal explanation of supported formats and processing behavior

The file display field should look like a calm status surface, not like a generic browser-native input.

The primary submit button should remain visually strongest on the page below the title area.

## Visual Direction

### Color

The palette should move toward restrained warm neutral tones:

- warm ivory backgrounds
- muted brown-gold accents
- dark brown text

Avoid bright, loud, or overly orange accents.

### Typography

Typography should feel editorial and premium:

- serif or display styling for the main Chinese title
- clean sans-serif for body and controls
- strong hierarchy between title, supporting copy, labels, and controls

### Brand Feel

The page should communicate:

- trustworthy
- formal
- premium
- structured

It should not communicate:

- playful
- experimental
- hacky
- prototype-like

## Responsive Behavior

On narrow screens:

- the large panel should reduce padding but preserve hierarchy
- the three process cards may stack vertically
- the upload area should stack cleanly
- the primary action must remain prominent and easy to tap

## Implementation Notes

Implementation should preserve the approved structure while replacing the current placeholder copy and undersized upload panel.

The frontend implementation should explicitly:

- remove `Phase 1`
- translate visible page copy into Chinese
- enlarge the panel and improve spacing
- rebuild the upload area so `选择文件` and `开始评估` have distinct roles and visual weights
- restyle the page toward a more premium commercial tone

## Final Decision

Approved direction:

- centered premium landing layout
- `需求评估平台` as the only main title
- formal, commercial Chinese copy
- three-stage process section
- upload area with separated secondary and primary actions
- warmer, more restrained premium visual language
