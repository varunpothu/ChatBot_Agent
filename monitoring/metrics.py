from dataclasses import dataclass

@dataclass
class Metrics:
    requests: int = 0
    successful_answers: int = 0
    abstentions: int = 0
    human_escalations: int = 0
    verification_failures: int = 0
    injection_blocks: int = 0
    rate_limit_blocks: int = 0
    budget_blocks: int = 0
    cache_hits: int = 0
    fast_path_answers: int = 0
    llm_calls: int = 0
    translation_calls: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    translation_characters: int = 0
    tts_characters: int = 0
    total_latency_ms: float = 0

    def record(self,event:str,latency_ms:float=0,**usage):
        if event in {"answer","abstention"}:
            self.requests+=1;self.total_latency_ms+=latency_ms
        if event=="answer":self.successful_answers+=1
        if event=="abstention":self.abstentions+=1
        if event=="human_escalation":self.human_escalations+=1
        if event=="verification_failure":self.verification_failures+=1
        if event=="security_block":self.injection_blocks+=1
        if event=="rate_limit_block":self.rate_limit_blocks+=1
        if event=="budget_block":self.budget_blocks+=1
        if event=="cache_hit":self.cache_hits+=1
        if event=="fast_path":self.fast_path_answers+=1
        if event=="llm_call":self.llm_calls+=1
        if event=="translation_call":self.translation_calls+=1
        self.estimated_input_tokens+=int(usage.get("input_tokens",0))
        self.estimated_output_tokens+=int(usage.get("output_tokens",0))
        self.translation_characters+=int(usage.get("translation_characters",0))
        self.tts_characters+=int(usage.get("tts_characters",0))

    def snapshot(self):
        return {
            "requests":self.requests,"successful_answers":self.successful_answers,"abstentions":self.abstentions,
            "human_escalations":self.human_escalations,"verification_failures":self.verification_failures,
            "injection_blocks":self.injection_blocks,"rate_limit_blocks":self.rate_limit_blocks,
            "budget_blocks":self.budget_blocks,"cache_hits":self.cache_hits,
            "cache_hit_rate":round(self.cache_hits/self.requests,4) if self.requests else 0,
            "fast_path_answers":self.fast_path_answers,
            "fast_path_rate":round(self.fast_path_answers/self.requests,4) if self.requests else 0,
            "llm_calls":self.llm_calls,"llm_call_rate":round(self.llm_calls/self.requests,4) if self.requests else 0,
            "translation_calls":self.translation_calls,"translation_characters":self.translation_characters,
            "estimated_input_tokens":self.estimated_input_tokens,"estimated_output_tokens":self.estimated_output_tokens,
            "tts_characters":self.tts_characters,
            "average_latency_ms":round(self.total_latency_ms/self.requests,2) if self.requests else 0,
            "grounded_answer_rate":round(self.successful_answers/self.requests,4) if self.requests else 0,
            "abstention_rate":round(self.abstentions/self.requests,4) if self.requests else 0,
        }

metrics=Metrics()
