# Database Schema Documentation

## Tables Overview

### llm_requests
Primary table storing all intercepted LLM API calls.

**Key Fields:**
- `id` (UUID): Primary key
- `timestamp` (TIMESTAMPTZ): When the request occurred
- `src_ip` (TEXT): Internal IP address of requestor
- `provider` (TEXT): openai, anthropic, etc.
- `model` (TEXT): gpt-4, claude-3, etc.
- `prompt` (TEXT): User prompt (will be encrypted)
- `response` (TEXT): LLM response (will be encrypted)
- `tokens_prompt/response/total` (INTEGER): Token counts
- `risk_score` (INTEGER): 0-100 calculated risk score
- `is_flagged` (BOOLEAN): Whether request triggered rules
- `flag_reason` (TEXT): List of triggered rule names

### detection_rules
Configurable rules for flagging risky requests.

**Rule Types:**
- `keyword`: Exact keyword matching
- `regex`: Regular expression patterns
- `model_restriction`: Blocked model names
- `token_limit`: Maximum token thresholds

**Default Rules:**
- Critical keywords (password, secret, etc.) - 50 points
- Email patterns - 30 points
- Credit card patterns - 60 points
- IP addresses - 20 points
- Phone numbers - 15 points
- Token limits (>2000) - 25 points
- Restricted models - 20 points

### alerts
Tracks Slack/email notifications sent for flagged requests.

### user_sessions
Groups requests by IP address and 30-minute time windows for session analysis.

## Indexing Strategy
- Timestamp-based queries (dashboard views)
- IP-based filtering (user tracking)
- Provider/model filtering (analytics)
- Flagged requests (security review)
- Risk score sorting (priority triage)

## Data Retention
- Automatic cleanup function removes records older than 6 months
- Monthly partitioning for performance (to be implemented)
- Encrypted storage for sensitive prompt/response data

## Security Features
- UUID primary keys (no sequential IDs)
- Prepared for column-level encryption on prompt/response
- Role-based access controls
- Audit trails with created_at/updated_at timestamps