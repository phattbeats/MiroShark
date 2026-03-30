"""
Template API routes — serves preset simulation templates
"""

import os
import json
from flask import jsonify

from . import templates_bp
from ..utils.logger import get_logger

logger = get_logger('miroshark.api.templates')

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'preset_templates')


def _load_templates():
    """Load all template JSON files from the templates directory."""
    templates = []
    if not os.path.isdir(TEMPLATES_DIR):
        return templates

    for filename in sorted(os.listdir(TEMPLATES_DIR)):
        if not filename.endswith('.json'):
            continue
        filepath = os.path.join(TEMPLATES_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template = json.load(f)
            templates.append(template)
        except Exception as e:
            logger.warning(f"Failed to load template {filename}: {e}")

    return templates


@templates_bp.route('/list', methods=['GET'])
def list_templates():
    """
    List all available simulation templates.

    Returns a summary of each template (without the full seed_document)
    so the frontend can render a gallery.
    """
    try:
        templates = _load_templates()

        summaries = []
        for t in templates:
            summaries.append({
                "id": t["id"],
                "name": t["name"],
                "category": t.get("category", ""),
                "description": t.get("description", ""),
                "icon": t.get("icon", ""),
                "difficulty": t.get("difficulty", "medium"),
                "estimated_agents": t.get("estimated_agents", 0),
                "estimated_rounds": t.get("estimated_rounds", 0),
                "platforms": t.get("platforms", []),
                "tags": t.get("tags", []),
            })

        return jsonify({
            "success": True,
            "data": summaries,
            "count": len(summaries)
        })

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@templates_bp.route('/<template_id>', methods=['GET'])
def get_template(template_id: str):
    """
    Get a single template by ID, including the full seed_document and
    simulation_requirement for use in the creation flow.
    """
    try:
        filepath = os.path.realpath(os.path.join(TEMPLATES_DIR, f"{template_id}.json"))
        if not filepath.startswith(os.path.realpath(TEMPLATES_DIR)):
            return jsonify({
                "success": False,
                "error": "Invalid template ID"
            }), 400
        if not os.path.exists(filepath):
            return jsonify({
                "success": False,
                "error": f"Template not found: {template_id}"
            }), 404

        with open(filepath, 'r', encoding='utf-8') as f:
            template = json.load(f)

        return jsonify({
            "success": True,
            "data": template
        })

    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
