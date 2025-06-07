# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of interactive HTML-based educational games that teach learning theory concepts. Each game is a standalone HTML file with embedded JavaScript and CSS that can be opened directly in a web browser.

## Architecture

### Game Structure
- **Standalone HTML files**: Each game is self-contained with inline CSS and JavaScript
- **No external dependencies**: Except for CDN-hosted libraries like Chart.js in some games
- **Interactive canvas-based UI**: Games use HTML5 canvas for drawing and user interaction
- **Educational focus**: Each game teaches specific learning theory concepts through hands-on experience

### Current Games
- `vapnik-chervonenkis-game.html`: Interactive VC-dimension game teaching the concept of "shattering" datasets
- `rademacher-calculator.html`: Numerical calculator for Rademacher complexity with visualizations

### Common Patterns
- Dark/gradient themed UI with glassmorphism effects
- Canvas-based interactive elements with mouse event handling
- Real-time calculation and visualization updates
- Educational explanations embedded alongside interactive elements
- Responsive design with CSS Grid and Flexbox

## Development Commands

### Deployment
The project auto-deploys to `learning-theory.arithmetic.guru` via GitHub Actions when pushing to `main` branch.

### Local Development
- Open HTML files directly in browser for testing
- No build process required - all games are standalone
- Use browser developer tools for debugging

### Manual Deployment
The GitHub Action performs these steps:
1. Converts README.md to index.html using pandoc
2. Deploys all *.html files via SCP to the web server

## Adding New Games

When creating new learning theory games:
1. Follow the existing self-contained HTML structure
2. Include comprehensive educational explanations alongside interactivity
3. Use consistent visual theming (dark backgrounds, glassmorphism, gradient accents)
4. Implement canvas-based interactions for data manipulation
5. Add the new game to README.md
6. Update TODO.md with completion status

## Project Maintainer Notes

### Research Focus (Greg Baker)
- **P-adic machine learning**: Exploring ML methods in non-Archimedean settings
- **Ultrametric spaces**: ML applications in ultrametric geometries
- **Narrative learning**: Language models generating and testing hypotheses without explicit computational models

### Pedagogical Philosophy
- **SVM skepticism**: SVMs are primarily academic/lecture tools, rarely used for real-world problems
- Focus on practically relevant learning theory concepts
- Emphasis on intuition-building over algorithm implementation

## Game-Specific Notes

### VC-Dimension Game
- Implements point classification with line/circle/rectangle separators
- Teaches shattering concept through interactive point coloring
- Uses mouse events for point interaction and classifier drawing

### Rademacher Calculator
- Performs numerical Rademacher complexity calculations
- Uses Chart.js for data visualization
- Implements polynomial fitting and statistical analysis in pure JavaScript
- Heavy computational work done client-side with progress indicators