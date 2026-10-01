import os

class AmazonTranslateProvider:
    """Optional AWS translation adapter for multilingual fast answers."""
    def __init__(self, region: str | None = None):
        import boto3
        self.client=boto3.client("translate",region_name=region or os.getenv("AWS_REGION","eu-west-2"))

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text
        response=self.client.translate_text(
            Text=text[:5000],
            SourceLanguageCode=source_language,
            TargetLanguageCode=target_language,
        )
        return response["TranslatedText"].strip()
