# Multilingual conversation architecture

Language is a first-class conversation attribute.

## Student experience

The UI exposes an Auto-detect option plus a list of supported languages. The selected language is carried with the conversation request. Browser speech recognition uses the corresponding speech locale.

## Cost-optimized text flow

English knowledge lookup:
retrieve -> extract -> verify -> answer

Non-English knowledge lookup:
translate query to source language -> retrieve -> extract -> verify -> translate verified answer -> answer

Only the query and final verified answer are translated. The knowledge source remains authoritative.

## Complex multilingual questions

For synthesis questions, CoachAI uses one cloud generation call to create a grounded source-language answer and then translates the verified answer. This is deliberately safer than asking one model call to both reason and self-verify across languages.

## Auto-detection

Script detection is deterministic for major Indic scripts, Arabic-derived scripts, Japanese and Chinese. Latin-script languages default to English (UK); users can choose Spanish, French, German and other Latin-script languages explicitly.

Arabic and Urdu use partially overlapping scripts. CoachAI detects common Urdu-specific characters when available, but explicit language selection remains the reliable path for ambiguous Arabic-script input.

## Voice

Browser speech is the default low-cost option. The browser receives the selected language code and uses an installed voice for that locale where available.

Amazon Polly is optional. Polly supports a broad set of languages, including Hindi, English, Spanish, French, German, Italian, Portuguese, Japanese, Chinese and Arabic. Not every Transcribe/Translate language has a corresponding Polly voice, so the API exposes provider capability metadata and fails cleanly when cloud voice support is unavailable.

## Translation provider

Set TRANSLATION_PROVIDER=aws_translate to enable Amazon Translate for the non-English fast path. When it is disabled, the system fails closed for non-English requests rather than pretending it can safely translate.

## Cost controls

Translated queries and answers are cached. Repeated multilingual questions therefore reuse the verified response instead of repeatedly paying for translation.

The dashboard reports translation calls and translated characters separately from LLM calls and model tokens.
