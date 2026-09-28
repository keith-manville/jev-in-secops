# Jev for Google SecOps SOAR

A Google SecOps SOAR response integration for **Jev**, the decision model from
[TypeSafe AI](https://typesafe.ai). Jev answers typed questions about any text or JSON
with calibrated probabilities instead of generated prose, so playbooks can branch on
its answers directly.

The integration follows the [Content Hub](https://github.com/chronicle/content-hub)
layout. The folder `content/response_integrations/third_party/community/jev/` can be
copied as is into a fork of `chronicle/content-hub`.

## Prerequisite: a TypeSafe account and API key

You need a TypeSafe API key to use this integration.

1. Create an account at **https://console.typesafe.ai/** (Google sign-in or email code).
2. In the console, create an API key and copy it.
3. In Google SecOps, open **Content Hub > Response Integrations**, install **Jev**,
   and configure it:

| Parameter | Mandatory | Default | Description |
| --- | --- | --- | --- |
| API Root | Yes | `https://api.typesafe.ai` | TypeSafe API root URL. |
| API Key | Yes | | The API key from console.typesafe.ai. |
| Default Model | No | `jev-latest` | Model or alias used when an action does not set "Model". Pin a version such as `jev-1.13.0` to keep answers stable across releases. |
| Verify SSL | No | `true` | Validate the TypeSafe SSL certificate. |

4. Run the **Ping** action to confirm the key works. An invalid key fails with a
   message that points back to console.typesafe.ai.

## Actions

Every action that asks Jev a question returns the full API response as its JSON
result, adds a "Jev Answers" table to the case wall, and sets the action result to the
decision itself so playbook conditions can use it.

| Action | Action result | What it does |
| --- | --- | --- |
| Ping | `is_success` | Validates connectivity and the API key (`GET /v1/models`). |
| List Models | `is_success` | Lists the models and aliases the key can use. |
| Ask Yes No Question | `is_yes` (true/false) | Asks a yes/no ("noul") question. True when the yes probability is at or above "Threshold" (default 0.5). |
| Ask Choice Question | `choice` (option) | Picks one option from a comma-separated list or a JSON object of option to description (2 to 255 options). |
| Ask Score Question | `score` (number) | Rates content along ordered levels, lowest first (2 to 10 levels). |
| Evaluate Questions | `is_success` | Sends a JSON map of any mix of noul, choice and score questions in one request. |
| Triage Alert | `recommended_action` | Builds a state from the current alert (name, rule, product, severity, entities, security event fields) and asks whether it is malicious, how severe it is, and whether to `close`, `investigate`, `escalate` or `contain`. Add your own questions with "Custom Questions". |

The question actions take a **State** parameter: plain text, or a JSON object or
array (sent to Jev as structured data). Placeholders such as
`[Event.additional_properties]` work. Each of them also takes an optional **Model**
that overrides the integration default.

### Example: route a phishing report

* **Ask Choice Question**
  * State: `[Event.email_subject] [Event.email_body]`
  * Question: `What kind of email is this?`
  * Options: `{"phishing": "Credential theft or malicious link", "spam": "Unwanted marketing", "benign": "Legitimate business email"}`
* Playbook condition on the action result: `phishing` goes to the phishing branch.

### Example: Evaluate Questions

```json
{
  "is_phishing": {"type": "noul", "instructions": "Is this a phishing attempt?"},
  "category": {
    "type": "choice",
    "instructions": "What kind of message is this?",
    "criteria": {"phishing": null, "spam": null, "business": null}
  },
  "risk": {
    "type": "score",
    "instructions": "How risky is this message?",
    "criteria": ["No risk", "Low", "Medium", "High"]
  }
}
```

See the [TypeSafe API reference](https://docs.typesafe.ai/api) for the full question format.

## Behavior notes

* Requests that get `429 Too Many Requests` or `529 Overloaded` are retried up to 3
  times with exponential backoff, honoring `retry-after`.
* Jev accepts text only and has a context limit (32k tokens for the state plus the
  longest question). **Triage Alert** includes at most "Max Events" events (default 10)
  and drops more events if the state is still too large.
* Alert content is sent to TypeSafe for evaluation. Review the
  [TypeSafe data handling terms](https://docs.typesafe.ai/legal) before using it with
  sensitive data.

## Installing as a custom integration (ZIP)

Google SecOps imports custom integrations as a ZIP package. Build it with the
Content Hub `mp` tool:

```bash
git clone https://github.com/chronicle/content-hub.git
cd content-hub
cp -r <this repo>/content/response_integrations/third_party/community/jev \
      content/response_integrations/third_party/community/
pip3 install -e ./packages/mp       # macOS: pip3, or: uv pip install -e ./packages/mp
mp config --root-path .
mkdir -p dist                       # mp pack does not create the output folder
mp pack integration jev --non-interactive --dst ./dist
```

This creates `dist/Jev<date>.zip`. Then in Google SecOps:

1. Go to **Response > IDE**, click the import icon and upload the ZIP.
2. Configure the integration (API Key from https://console.typesafe.ai/) and run **Ping**.

## Development

The integration uses the Content Hub tooling (`mp`), TIPCommon and the
`integration_testing` mocks. Tests never call the real API.

```bash
# From the root of a chronicle/content-hub checkout
cp -r <this repo>/content/response_integrations/third_party/community/jev \
      content/response_integrations/third_party/community/
uv pip install -e ./packages/mp
mp config --root-path .
mp check content/response_integrations/third_party/community/jev
mp validate integration jev
mp test --integration jev
mp build -i jev
```

Current status: `mp check`, `mp validate` (23/23), `mp test` (25/25) and `mp build`
all pass.
