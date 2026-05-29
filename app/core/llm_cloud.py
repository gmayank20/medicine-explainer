try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            token=HF_API_TOKEN,
            provider="hf-inference"
        )

        messages = [
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"}
        ]

        response = client.chat_completion(
            messages=messages,
            max_tokens=400,
            temperature=0.1
        )

        explanation = response.choices[0].message.content
        explanation = apply_safety_filter(explanation)

        cache_explanation(
            medicine_name, explanation,
            "mistral-7b-instruct-hf"
        )

        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=explanation,
            was_cached=False,
            model_used="mistral-7b-instruct-hf",
            safety_footer=SAFETY_FOOTER
        )

    except Exception as e:
        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=f"Debug error for '{medicine_name}': {str(e)}",
            was_cached=False,
            model_used="error",
            safety_footer=SAFETY_FOOTER
        )