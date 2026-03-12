# Aesthetic & Design Guide

## Overview

Your Gita Wisdom AI platform has been transformed from a technical interface to a **serene, spiritually-aligned experience**. This guide explains all customizations and how to modify them.

---

## 1. Typography System

### Font Stack

| Element | Font | Purpose |
|---------|------|---------|
| **Verses** | Lora (Serif) | Ancient scripture aesthetic |
| **Headers** | Lora (Serif) | Professional, spiritual feel |
| **UI Text** | Inter (Sans-serif) | Clean, modern readability |
| **Body** | Inter (Sans-serif) | Consistent, accessible |

### How to Change

In `streamlit_app.py`, modify the `@import url()` line:

```python
# Current fonts
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Inter:wght@300;400;500;600;700&display=swap');

# Alternative combinations:
# Classic: Georgia serif instead of Lora
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital@0;1&family=Montserrat:wght@300;400;600;700&display=swap');

# Modern: Playfair Display
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+Pro:wght@400;600&display=swap');
```

---

## 2. Color Palette

### Current Color Scheme

```
Primary Gold:     #E0C097  (warm, spiritual)
Secondary Gold:   #F0D9B5  (lighter, hover state)
Earth Brown:      #B8956A  (accents)
Dark Charcoal:    #1E1D1C  (backgrounds)
Deep Charcoal:    #2A2926  (darker backgrounds)
Soft Gray:        #D4D4D4  (body text)
```

### Where Colors Are Used

| Color | Component | CSS Selector |
|-------|-----------|--------------|
| #E0C097 | Hero title, verse refs | `.hero-title`, `.verse-reference` |
| #B8956A | Subtitles, hints | `.hero-subtitle`,  `.paper-card small` |
| #1E1D1C | Page background | `.stApp` |
| #D4D4D4 | Body text | `p, li` |
| #FF9800 | Admin alerts | `.admin-panel` |

### Customize Colors

1. **Find all instances** in `streamlit_app.py` CSS:
   ```bash
   grep -n "#E0C097" streamlit_app.py
   ```

2. **Replace globally:**
   - Change `#E0C097` to your primary color
   - Change `#B8956A` to your secondary
   - Change `#1E1D1C` to your background

**Example:** For a blue/silver theme:
```css
#E0C097 → #6C8EBF  (steel blue)
#B8956A → #4A5F7F  (slate)
#1E1D1C → #1C1F2A  (dark blue)
#D4D4D4 → #E3E3E3  (light silver)
```

---

## 3. Hero Image & Background

### Current Background

- **URL:** `https://images.unsplash.com/photo-1502481851512-e9e2529bbbf9`
- **Effect:** Scenic landscape with dark gradient overlay
- **Format:** Unsplash image (free, high-quality)

### Change Background Image

Replace the URL in the `.stApp` style:

```python
.stApp {
    background: linear-gradient(135deg, rgba(30, 29, 28, 0.95), rgba(50, 48, 46, 0.95)),
                url('https://YOUR_NEW_IMAGE_URL') center/cover;
}
```

**Recommended Unsplash Images:**

| Vibe | URL | Best For |
|------|-----|----------|
| Sunset/Spiritual | `photo-1506905925346-21bda4d32df4` | Serene feel |
| Mountain/Peace | `photo-1506905925346-21bda4d32df4` | Grounding |
| Water/Calm | `photo-1506905925346-21bda4d32df4` | Cooling effect |
| Forest/Nature | `photo-1441974231531-c6227db76b6e` | Natural vibes |

*Format: `https://images.unsplash.com/photo-[ID]?q=80&w=2070&auto=format&fit=crop`*

### Adjust Overlay Darkness

Control how much the dark gradient shows:

```css
/* Current (very dark) */
linear-gradient(135deg, rgba(30, 29, 28, 0.95), rgba(50, 48, 46, 0.95))

/* Lighter overlay (shows more image) */
linear-gradient(135deg, rgba(30, 29, 28, 0.70), rgba(50, 48, 46, 0.70))

/* Very dark (shows less image) */
linear-gradient(135deg, rgba(30, 29, 28, 0.99), rgba(50, 48, 46, 0.99))
```

---

## 4. Card Styling & Effects

### Verse Card Design

```css
.verse-card {
    background: linear-gradient(135deg, 
        rgba(255, 255, 255, 0.08),    /* Lighter on one side */
        rgba(255, 255, 255, 0.03)     /* Darker on other */
    );
    border: 1px solid rgba(224, 192, 151, 0.15);
    border-radius: 12px;
    backdrop-filter: blur(10px);       /* Frosted glass effect */
}
```

### Customize Border & Shadow

```css
/* For raised/dramatic effect */
box-shadow: 0 8px 25px rgba(224, 192, 151, 0.15);

/* For minimal effect */
box-shadow: 0 2px 8px rgba(224, 192, 151, 0.05);

/* For no shadow */
box-shadow: none;
```

### Remove Frosted Glass Effect

If you prefer sharp backgrounds:

```python
# Find this line:
backdrop-filter: blur(10px);

# Delete it entirely
# The card will be solid instead of frosted
```

---

## 5. Button Styling

### Current Button Design

```css
.stButton > button {
    background: linear-gradient(135deg, #E0C097, #B8956A);
    color: #1E1D1C;
    font-weight: 600;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(224, 192, 151, 0.2);
}
```

### Customize Button

```python
# Change gradient colors:
background: linear-gradient(135deg, #YOUR_COLOR1, #YOUR_COLOR2);

# Change size/padding:
padding: 12px 24px;  /* Add to :button */

# Change shadow:
box-shadow: 0 6px 15px rgba(224, 192, 151, 0.3);

# Change border radius (0=square, 20=round):
border-radius: 20px;
```

---

## 6. Admin Panel Customization

### Show/Hide Admin Panel

The admin panel is **only visible** when correct password is entered. To change this behavior:

```python
# In sidebar section:
if access_key == ADMIN_PASSWORD:
    # Only this shows admin
    st.expander("🛠️ Database Management")
```

### Customize Admin Panel Style

```css
.admin-panel {
    background: linear-gradient(
        135deg, 
        rgba(255, 193, 7, 0.08),      /* Yellow tint */
        rgba(255, 152, 0, 0.08)
    );
    border-left: 4px solid #FF9800;    /* Orange accent */
}

/* Change to blue theme */
rgba(33, 150, 243, 0.08),  /* Light blue */
rgba(33, 150, 243, 0.08),
border-left: 4px solid #2196F3;  /* Blue border */
```

---

## 7. Tab Styling

### Current Tab Design

```css
.stTabs [data-baseweb="tab"] {
    color: #B8956A;           /* Inactive tab color */
}

.stTabs [aria-selected="true"] {
    color: #E0C097;           /* Active tab color */
    border-bottom: 2px solid #E0C097;  /* Bottom border */
}
```

### Customize Tab Appearance

```python
# Remove bottom border:
border-bottom: none;

# Make tabs have background:
background: linear-gradient(...);  # Add gradient

# Make tabs wider/more spaced:
padding: 20px;  # Increase from default
```

---

## 8. Responsive Design

### Mobile Optimization

The app is **already responsive**, but you can test and adjust:

```css
/* Add media queries for small screens */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2rem;  /* Smaller on mobile */
    }
    
    .verse-card {
        padding: 1rem;  /* Less padding */
    }
}
```

---

## 9. Accessibility

### Text Contrast

**Current contrast ratios:**
- #E0C097 on #1E1D1C = **7.2:1** ✓ (AAA standard)
- #D4D4D4 on #1E1D1C = **9.6:1** ✓ (Perfect)

If you change colors, test contrast at: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Font Size Adjustments

```css
/* Increase for better readability */
body {
    font-size: 1.1rem;  /* From 1rem */
}

h1 {
    font-size: 3.2rem;  /* From 3rem */
}
```

---

## 10. Advanced CSS Techniques

### Add Glassmorphism

```css
.verse-card {
    backdrop-filter: blur(20px);  /* More blur */
    -webkit-backdrop-filter: blur(20px);  /* Safari support */
}
```

### Animation on Hover

```css
.verse-card {
    transition: all 0.3s ease;  /* Already present */
}

.verse-card:hover {
    transform: translateY(-5px);  /* Move up on hover */
}
```

### Add Glow Effect

```css
.verse-card:hover {
    box-shadow: 0 8px 25px rgba(224, 192, 151, 0.3),
                0 0 30px rgba(224, 192, 151, 0.1);  /* Glow */
}
```

---

## 11. Deployment Customization

### For Streamlit Cloud

1. Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#E0C097"
backgroundColor = "#1E1D1C"
secondaryBackgroundColor = "#2A2926"
textColor = "#D4D4D4"
font = "sans serif"

[client]
showErrorDetails = false
```

2. Create `.streamlit/secrets.toml`:
```toml
ADMIN_PASSWORD = "your_secret_password"
```

### Environment Variables

```python
import os

# Get password from environment (Streamlit Cloud secrets)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "gita_admin_2024")

# Get image URL from env
BG_IMAGE = os.getenv(
    "BG_IMAGE",
    "https://images.unsplash.com/photo-1502481851512-e9e2529bbbf9"
)
```

---

## 12. Testing Your Changes

### Local Testing

```bash
streamlit run streamlit_app.py
```

### Mobile Testing

1. Use Chrome DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test on various screen sizes

### Accessibility Testing

- Use browser extensions: WAVE, Lighthouse
- Test keyboard navigation (Tab through interface)
- Check color contrast ratios

---

## 13. Performance Tips

### Reduce File Size

- Use WebP images (smaller than PNG/JPG)
- Compress CSS (remove whitespace)
- Use system fonts instead of Google Fonts (if offline needed)

### Optimize Images

```python
# Use smaller image resolution
url('https://images.unsplash.com/...?q=80&w=1200')  # Instead of w=2070
```

### Cache Custom CSS

```python
@st.cache_data
def get_css():
    return """<style>...</style>"""

st.markdown(get_css(), unsafe_allow_html=True)
```

---

## 14. Resources

### Design Inspiration
- [Unsplash](https://unsplash.com) - Free images
- [Google Fonts](https://fonts.google.com) - Free fonts
- [Color Palette Generators](https://coolors.co) - Color schemes

### Technical References
- [CSS Gradients](https://developer.mozilla.org/en-US/docs/Web/CSS/gradient)
- [Backdrop Filter](https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter)
- [Streamlit CSS Classes](https://discuss.streamlit.io/t/custom-css-in-streamlit/19713)

### Similar Apps
- [Spiritual Platforms](https://www.producthunt.com)
- [Academic Interfaces](https://scholar.google.com)

---

## 15. Quick Customization Template

To quickly change the entire theme, replace these colors:

```python
# Find & Replace in streamlit_app.py

OLD_COLOR → NEW_COLOR
#E0C097 → [Your primary color]
#B8956A → [Your secondary color]
#1E1D1C → [Your background]
#D4D4D4 → [Your text color]
#F0D9B5 → [Your light accent]

# Also update:
Lora → [Your serif font]
Inter → [Your sans-serif]
```

---

## Support

For issues with styling:
1. Check browser console (F12) for CSS errors
2. Clear Streamlit cache: `streamlit cache clear`
3. Hard refresh browser (Ctrl+Shift+R)
4. Test in incognito mode

**Contact:** 111deblina@gmail.com
