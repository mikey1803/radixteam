# OpenAI API Setup Guide - Resume Parser

## 🔍 Issue Identified

**Error:** `LLM extraction failed, falling back to rules`

**Root Cause:** OpenAI API quota exceeded (Error 429: Insufficient Quota)

Your API key is valid but has exceeded its usage quota or doesn't have billing configured.

---

## ✅ Current Status

- ✅ Your resume parsing API is **working correctly**
- ✅ It automatically falls back to rule-based extraction when LLM is unavailable
- ✅ The endpoint returns 201 Created successfully
- ⚠️ However, you're getting **basic extraction** instead of **AI-powered extraction**

---

## 🛠️ Solutions

### Option 1: Add Billing to Your OpenAI Account (Recommended)

1. Visit https://platform.openai.com/account/billing
2. Add a payment method
3. Set up billing limits (optional but recommended)
4. Your API will start working immediately after billing is configured

**Cost:** Very affordable for resume parsing
- `gpt-4o-mini` model: ~$0.15 per 1M input tokens
- Average resume: ~500-1000 tokens = **$0.0001-$0.0002 per resume**

### Option 2: Use a Different API Key

If you have another OpenAI account with available quota:

1. Get a new API key from https://platform.openai.com/api-keys
2. Update your `.env` file:
   ```env
   OPENAI_API_KEY=sk-proj-your-new-key-here
   ```
3. Restart your server

### Option 3: Use an Alternative LLM Provider

You can use OpenAI-compatible providers like:

**Groq (Fast & Free tier available):**
```env
OPENAI_API_KEY=gsk_your-groq-key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.1-70b-versatile
```

**Together.ai:**
```env
OPENAI_API_KEY=your-together-key
OPENAI_BASE_URL=https://api.together.xyz/v1
OPENAI_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

**Local LLM with Ollama:**
```env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1
```

### Option 4: Continue with Rule-Based Extraction

The system is already working with rule-based extraction. This is free and works reasonably well for:
- Basic resume parsing
- Extracting contact info, skills, experience
- Simple structured data

**Limitations:**
- Less accurate than AI parsing
- May miss nuanced information
- Cannot infer context as well as LLM

---

## 🧪 Testing Your Setup

Run the test script to verify your OpenAI configuration:

```bash
python test_openai_connection.py
```

This will show you:
- ✅ If your API key is valid
- ✅ If you have quota available
- ✅ If the model is accessible
- ❌ Specific error messages if something is wrong

---

## 📊 What Changed

I've improved the error handling in your resume parser to:

1. ✅ **Better error messages** - Now clearly identifies quota issues
2. ✅ **Graceful fallback** - Automatically uses rule-based parsing when LLM fails
3. ✅ **Detailed logging** - Shows specific error types (authentication, quota, network, etc.)
4. ✅ **Markdown cleanup** - Handles LLM responses with markdown code blocks
5. ✅ **JSON mode compatibility** - Automatically retries without JSON mode if not supported
6. ✅ **API key validation** - Strips whitespace and validates before use

---

## 📝 Configuration Examples

### Minimal (Current Setup)
```env
OPENAI_API_KEY=sk-proj-your-key-here
```

### With Custom Model
```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o  # More accurate but more expensive
```

### With Alternative Provider
```env
OPENAI_API_KEY=your-provider-key
OPENAI_BASE_URL=https://api.provider.com/v1
OPENAI_MODEL=provider-model-name
```

---

## 🚀 Next Steps

1. **Choose one of the solutions above**
2. **Update your `.env` file if needed**
3. **Restart your server**: `Ctrl+C` then restart
4. **Test the endpoint** by uploading a resume
5. **Check the logs** - you should see "LLM extraction completed successfully"

---

## 📞 Need Help?

- OpenAI Billing: https://platform.openai.com/account/billing
- OpenAI API Keys: https://platform.openai.com/api-keys
- OpenAI Docs: https://platform.openai.com/docs/
- Check Usage: https://platform.openai.com/usage

---

## 💡 Current vs Enhanced Parsing

**Rule-Based (Current):**
```json
{
  "personal_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@email.com",
    "phone": "+1234567890",
    "location": null,
    "headline": null
  },
  "skills": [
    {"name": "Python", "category": null, "proficiency": null}
  ]
}
```

**AI-Powered (With Working OpenAI):**
```json
{
  "personal_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@email.com",
    "phone": "+1 (234) 567-8890",
    "location": "San Francisco, CA",
    "headline": "Senior Software Engineer"
  },
  "skills": [
    {"name": "Python", "category": "Programming", "proficiency": "Expert"}
  ],
  "summary": "Experienced software engineer with 10+ years...",
  "experience": [/* detailed work history */],
  "education": [/* complete education info */]
}
```

---

**Files Modified:**
- ✅ `backend/modules/resume_parser/extractor.py` - Enhanced error handling
- ✅ `test_openai_connection.py` - Created for testing API connectivity
