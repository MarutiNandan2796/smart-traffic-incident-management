import json
import os
import urllib.error
import urllib.request
from django.conf import settings


def get_gemini_api_key():
    """Retrieve the Gemini API key from settings or environment."""
    key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
    return key.strip() if key else ''


def is_gemini_configured():
    """Check if a non-empty Gemini API key is configured."""
    return bool(get_gemini_api_key())


def generate_gemini_content(prompt, system_instruction=None):
    """
    Direct REST client for Google Gemini 1.5 Flash.
    Lightweight, fast, zero heavy dependencies.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return {
            'success': False,
            'configured': False,
            'error': 'Gemini API key is not configured. Add your GEMINI_API_KEY in .env or the AI modal to activate.',
            'text': None,
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 900,
        }
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=14) as response:
            res_body = response.read().decode('utf-8')
            parsed = json.loads(res_body)
            candidates = parsed.get('candidates', [])
            if candidates and 'content' in candidates[0]:
                parts = candidates[0]['content'].get('parts', [])
                if parts and 'text' in parts[0]:
                    return {'success': True, 'configured': True, 'text': parts[0]['text'], 'error': None}
            return {'success': False, 'configured': True, 'error': 'No content returned from Gemini model.', 'text': None}
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            err_msg = err_body.get('error', {}).get('message', str(e))
        except Exception:
            err_msg = str(e)
        return {'success': False, 'configured': True, 'error': f'Gemini API error ({e.code}): {err_msg}', 'text': None}
    except Exception as e:
        return {'success': False, 'configured': True, 'error': f'Connection error: {str(e)}', 'text': None}


def analyze_accident_report(accident):
    """Generate professional road safety analysis and forensic recommendations."""
    prompt = (
        f"You are a Senior Municipal Road Safety Engineer & Traffic Police Accident Investigator.\n"
        f"Analyze this verified road accident case file:\n\n"
        f"• Incident Case ID: #{accident.id}\n"
        f"• Title: {accident.title}\n"
        f"• Location: {accident.location.name} ({accident.location.zone} Zone)\n"
        f"• Severity: {accident.severity}\n"
        f"• Vehicles Involved: {accident.vehicles_involved}\n"
        f"• Human Casualties / Injuries: {accident.injuries}\n"
        f"• Incident Log: {accident.description}\n\n"
        f"Please provide a structured technical report containing:\n"
        f"1. **Root Cause Hypotheses** (e.g. speed mismatch, geometric junction flaw, signal violation, weather/visibility)\n"
        f"2. **Immediate Civil Engineering Measures** (e.g. rumble strips, high-friction surfacing, signboards, lighting)\n"
        f"3. **Police Enforcement Action Plan** (e.g. speed interceptors, breathalyzer patrol, signal re-timing)\n"
        f"4. **Long-Term Preventive Recommendation**\n\n"
        f"Format clearly using clean markdown bullet points."
    )
    sys_instruction = "You are an expert civic transport and traffic surveillance AI advisor for smart city authorities."
    return generate_gemini_content(prompt, sys_instruction)


def draft_traffic_advisory(topic, location_name="City Corridors", priority="Warning"):
    """Draft a professional, broadcast-ready public traffic alert."""
    prompt = (
        f"Generate a concise, professional public traffic advisory announcement.\n"
        f"• Topic / Situation: {topic}\n"
        f"• Corridor: {location_name}\n"
        f"• Advisory Level: {priority}\n\n"
        f"Output should include:\n"
        f"1. Broadcast Headline (bold, punchy)\n"
        f"2. Advisory Message (clear instructions for drivers, estimated impact, suggested alternate routes)\n"
        f"Keep the tone authoritative, clear, and citizen-friendly (within 100 words)."
    )
    return generate_gemini_content(prompt, "You are a Municipal Traffic Authority Communications Officer.")


def copilot_query(query, summary_context=""):
    """Interactive TrafficSafe AI Copilot for operational queries."""
    prompt = (
        f"Municipal Traffic Operational Context:\n{summary_context}\n\n"
        f"User / Officer Query:\n{query}\n\n"
        f"Provide a concise, helpful, and technically accurate answer regarding road safety, congestion mitigation, traffic engineering, or incident investigation."
    )
    return generate_gemini_content(prompt, "You are TrafficSafe Copilot, an AI assistant for municipal traffic management.")
