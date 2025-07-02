# TEMPLATES DIRECTORY - IMPORTANT GUIDELINES

## WARNING

Only the following templates should be used for the Prime Agent UI:

1. `autowave.html` - The main template for the Prime Agent UI
2. `layout.html` - The base layout template
3. `live_browser_tab.html` - The template for the Live Browser tab

## Important Guidelines

1. **DO NOT** create new templates
2. **DO NOT** modify any templates in the archive directory
3. **DO NOT** create routes that render archived templates
4. **DO NOT** move archived templates back to the main templates directory

## Why This Matters

Using multiple templates has caused significant confusion and wasted development time. By restricting development to only the autowave template, we ensure:

1. All changes are applied to the correct template
2. No duplicate templates are created
3. No confusion about which template is being used
4. Consistent user experience

## If You Need to Make UI Changes

Always make changes to the `autowave.html` template only. Do not create new templates or modify archived templates.

## Archived Templates

All other templates have been moved to the `archive` directory and should not be used.
