# Data + Screening Tools Jekyll Site

This is a Jekyll-based website for Data + Screening Tools, created from crawled pages of the original site at https://screening-tools.com.

## Project Structure

- `_config.yml` - Jekyll configuration
- `_layouts/` - Template layouts
- `_includes/` - Reusable components
- `_tools/` - Tool collection files
- `assets/` - CSS, JavaScript, and images
- Various markdown files for pages

## Setup and Installation

1. Make sure you have Ruby and Bundler installed
2. Clone this repository
3. Run `bundle install` to install dependencies
4. Run `bundle exec jekyll serve` to start the development server
5. Visit `http://localhost:4000` in your browser

## Dependencies

- Jekyll 4.2.0
- jekyll-feed
- csv
- logger

## Adding New Tools

To add a new tool to the site:

1. Create a new markdown file in the `_tools/` directory
2. Add front matter with `layout: tool`, title, image, and link
3. Add the tool's description and details in markdown format

## License

This project is for demonstration purposes only. All content belongs to their respective owners.