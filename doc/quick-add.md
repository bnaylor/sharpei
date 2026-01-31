# Quick-Add Syntax

Sharpei supports a quick-add syntax that lets you create tasks with priority, hashtags, due dates, and categories all from the main "Add a task..." input field.

## Syntax Overview

```
Task title !priority #tag1 #tag2 @date >Category
```

Elements can appear in any order. The title is everything that's not a special token.

## Elements

### Priority

Set task priority using `!high` or `!low`:

| Syntax | Priority | Shorthand |
|--------|----------|-----------|
| `!high` | High (P0) | `!h` |
| `!low` | Low (P2) | `!l` |
| *(omit)* | Normal (P1) | - |

**Examples:**
```
Urgent bug fix !high
Someday maybe !low
Regular task
```

### Hashtags

Add hashtags using `#tag`:

```
Weekly review #recurring #planning
Bug fix #frontend #urgent
```

Multiple hashtags are supported. They appear as clickable badges on the task.

### Due Date

Set due dates using `@date`:

| Syntax | Meaning |
|--------|---------|
| `@today` | Today |
| `@tomorrow` | Tomorrow |
| `@monday` ... `@sunday` | Next occurrence of that weekday |
| `@+3d` | 3 days from now |
| `@+2w` | 2 weeks from now |
| `@2025-02-15` | Specific date (ISO format) |

**Weekday behavior:** `@monday` means the *next* Monday. If today is Tuesday, `@monday` is 6 days away, not yesterday.

**Examples:**
```
Call dentist @tomorrow
Weekly standup @monday
Project deadline @2025-03-01
Follow up @+3d
Quarterly review @+2w
```

### Category

Override the selected category using `>CategoryName`:

```
Expense report >Finance
Update docs >Engineering
```

If omitted, the task uses the currently selected category (or no category if "All Tasks" is selected).

**Note:** Category names are case-insensitive and must match an existing category.

## Combined Examples

```
Call dentist @tomorrow !high #health
→ Title: "Call dentist"
→ Priority: High
→ Due: Tomorrow
→ Tags: #health

Finish quarterly report >Work #q4 #important @friday
→ Title: "Finish quarterly report"
→ Category: Work
→ Tags: #q4 #important
→ Due: Next Friday

Buy groceries #errands @+2d !low
→ Title: "Buy groceries"
→ Priority: Low
→ Tags: #errands
→ Due: 2 days from now

Simple task without any syntax
→ Title: "Simple task without any syntax"
→ Priority: Normal (default)
```

## Tips

1. **Order doesn't matter** - Put elements wherever feels natural:
   ```
   !high Fix critical bug @today #urgent
   Fix critical bug #urgent !high @today
   ```
   Both create the same task.

2. **Title is what's left** - After parsing special tokens, the remaining text becomes the title. Extra whitespace is trimmed.

3. **Partial syntax works** - Use only what you need:
   ```
   Quick note                    # Just a title
   Meeting notes #work           # Title + tag
   Review PR @tomorrow           # Title + date
   ```

4. **Categories must exist** - The `>Category` syntax only works with categories you've already created.

5. **Hashtags without quick-add** - You can still add/edit hashtags in the expanded task details view.
