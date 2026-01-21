# PLAN: Split Sidebar into Two Floating Elements

## Goal

Restructure the navigation sidebar into two visually distinct floating glass elements:
1. **Hamburger Button** - A floating circle aligned vertically with the Header
2. **Menu Capsule** - A floating pill/capsule aligned vertically with the `.content` area

---

## Design Decisions

| Decision | Choice |
|----------|--------|
| Visual connection | Completely separate (no shared background) |
| Expansion behavior | Only menu expands; hamburger stays fixed size |
| Mobile behavior | Both fixed to viewport |
| Toggle action | Expands/collapses menu (icons always visible) |
| Alignment | Center-to-center (icons share horizontal axis) |
| Gap size | Same as header → content gap (`15px`) |
| Menu top alignment | Precisely matches `.content` top edge |
| Animation | **None** (instant state change) |
| Hamburger shadow | **None** |
| Hamburger background | Glass effect (no shadow) |
| Hamburger icon | Static ☰ (no change when expanded) |

---

## Architecture: CSS Grid Approach

### Current Structure
```
+layout.svelte
├── Navigation.svelte (single aside, manages both hamburger + menu)
├── Header.svelte
├── .content
└── Footer.svelte
```

### New Structure
```
+layout.svelte (CSS Grid: 3 rows × 2 columns)
├── HamburgerButton.svelte (row 1, col 1)
├── Header.svelte (row 1, col 2)
├── MenuCapsule.svelte (row 2, col 1)
├── .content (row 2, col 2)
└── Footer.svelte (row 3, col 2)
```

### Why CSS Grid?

Using CSS Grid at the layout level ensures:
1. **Perfect alignment** - Hamburger automatically aligns with Header row; Menu aligns with Content row
2. **No magic numbers** - No need to calculate pixel offsets for vertical positioning
3. **Responsive by design** - Grid handles the relationships, media queries only adjust grid behavior
4. **Separation of concerns** - Each component is independent; no shared state for positioning

---

## Grid Layout Design

### Desktop (> 900px)
```css
.app {
    display: grid;
    grid-template-columns: 80px 1fr;      /* Sidebar column | Content column */
    grid-template-rows: auto 1fr auto;    /* Header row | Content row | Footer row */
    min-height: 100vh;
    gap: 0 0;                             /* No gap; components handle their own spacing */
}
```

```
┌─────────────────────────────────────────────────────────┐
│                         .app                            │
├───────────┬─────────────────────────────────────────────┤
│   80px    │                    1fr                      │
├───────────┼─────────────────────────────────────────────┤  ← Row 1: auto
│   ( ☰ )   │  ┌─────────────────────────────────────┐    │
│ Hamburger │  │            Header                   │    │
│           │  └─────────────────────────────────────┘    │
├───────────┼─────────────────────────────────────────────┤  ← Row 2: 1fr
│  ┌─────┐  │  ┌─────────────────────────────────────┐    │
│  │ 🏠  │  │  │                                     │    │
│  │ ✈︎  │  │  │           .content                  │    │
│  │ 📚  │  │  │                                     │    │
│  │ 📊  │  │  │                                     │    │
│  │ ⚙️  │  │  │                                     │    │
│  └─────┘  │  └─────────────────────────────────────┘    │
│  Menu     │                                             │
├───────────┼─────────────────────────────────────────────┤  ← Row 3: auto
│           │              Footer                         │
└───────────┴─────────────────────────────────────────────┘
```

### Expanded State (> 900px)
When expanded, the sidebar column grows:
```css
.app.sidebar-expanded {
    grid-template-columns: 220px 1fr;
}
```

The menu capsule width grows to fill the wider column, revealing labels.

### Mobile (≤ 900px)
```css
.app {
    display: block; /* or grid with single column */
}

/* Both hamburger and menu become fixed */
.hamburger-button,
.menu-capsule {
    position: fixed;
    left: 0;
    z-index: 20;
}
```

---

## New Components

### 1. `HamburgerButton.svelte`

**Purpose:** Floating circle button to toggle menu expansion.

**Props:**
- `expanded: boolean` - Current expansion state (for potential styling)
- `ontoggle: () => void` - Callback when clicked

**Styling:**
```css
.hamburger {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--glass-bg-strong);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    /* No shadow */
    /* No animation/transition */
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    justify-self: center;  /* Center in grid cell */
    align-self: center;    /* Center in grid cell */
}
```

### 2. `MenuCapsule.svelte`

**Purpose:** Floating pill containing navigation icons/links.

**Props:**
- `expanded: boolean` - Whether to show labels
- `items: Array<{icon, label, href}>` - Menu items

**Styling:**
```css
.menu-capsule {
    width: 56px;
    background: var(--glass-bg-strong);
    backdrop-filter: blur(28px) saturate(160%);
    border: 1px solid var(--glass-border);
    border-radius: 32px;
    padding: 12px 0;
    box-shadow: var(--glass-shadow);
    justify-self: center;  /* Center in grid cell */
    align-self: start;     /* Align to top of grid cell */
    /* No width transition - instant change */
}

.menu-capsule.expanded {
    width: 196px;
    justify-self: start;
    margin-left: 12px;
}
```

---

## State Management

The expansion state needs to be shared between components. Options:

### Option A: Lift State to Layout (Recommended)
```svelte
<!-- +layout.svelte -->
<script>
    let sidebarExpanded = $state(false);
    const toggleSidebar = () => sidebarExpanded = !sidebarExpanded;
</script>

<div class="app" class:sidebar-expanded={sidebarExpanded}>
    <HamburgerButton expanded={sidebarExpanded} ontoggle={toggleSidebar} />
    <Header />
    <MenuCapsule expanded={sidebarExpanded} {items} />
    <div class="content">{@render children()}</div>
    <Footer />
</div>
```

### Option B: Svelte Store
Create a shared store in `$lib/stores/sidebar.ts`. Overkill for this use case.

**Recommendation:** Option A - simple, local state in the layout.

---

## Files to Create

| File | Purpose |
|------|---------|
| `site/src/components/HamburgerButton.svelte` | Floating hamburger circle |
| `site/src/components/MenuCapsule.svelte` | Floating menu pill |

## Files to Modify

| File | Changes |
|------|---------|
| `site/src/routes/+layout.svelte` | Replace grid layout; add state; import new components |
| `site/src/components/Navigation.svelte` | **Delete** (replaced by two new components) |

---

## Implementation Steps

### Step 1: Create `HamburgerButton.svelte`
- Simple button component
- Receives `expanded` and `ontoggle` props
- Glass background, no shadow, no animation
- Centers itself in grid cell

### Step 2: Create `MenuCapsule.svelte`
- Receives `expanded` and `items` props
- Contains the menu list with icons
- Shows labels when expanded
- No width transition (instant)
- Has shadow (`var(--glass-shadow)`)

### Step 3: Update `+layout.svelte`
- Change `.app` to 3-row × 2-column grid
- Add `sidebarExpanded` state
- Import and place `HamburgerButton` in row 1, col 1
- Import and place `MenuCapsule` in row 2, col 1
- Add `.sidebar-expanded` class to toggle column width
- Update media queries for mobile fixed positioning

### Step 4: Delete `Navigation.svelte`
- Remove the old component file
- Remove import from layout

### Step 5: Verify Alignment
- Hamburger should be vertically centered in the Header row
- Menu capsule top should align with `.content` top
- Icons should be horizontally centered in the 80px column

### Step 6: Test Mobile Behavior
- Both components fixed to left edge
- Hamburger at top
- Menu below with proper gap

---

## CSS Variables to Add

```css
:root {
    /* Existing... */
    
    /* Sidebar */
    --sidebar-width: 80px;
    --sidebar-width-expanded: 220px;
    --hamburger-size: 48px;
    --menu-icon-size: 40px;
    --menu-capsule-width: 56px;
    --menu-capsule-width-expanded: 196px;
}
```

---

## Testing Checklist

- [ ] Hamburger vertically centered in Header row
- [ ] Menu capsule top aligned with `.content` top  
- [ ] Both elements horizontally centered in sidebar column (collapsed)
- [ ] Icons share the same horizontal center axis
- [ ] No animation on expand/collapse (instant)
- [ ] Hamburger has glass background, no shadow
- [ ] Menu capsule has glass background with shadow
- [ ] Labels appear instantly when expanded
- [ ] Mobile: both elements fixed
- [ ] No horizontal overflow

---

## Open Questions (Resolved)

1. ~~Hamburger shadow?~~ → No shadow
2. ~~Animation?~~ → No animation
3. ~~Icon change on expand?~~ → No, stays as ☰

---

## Ready for Implementation

Confirm this plan is acceptable, then I will proceed with creating the components and updating the layout.
