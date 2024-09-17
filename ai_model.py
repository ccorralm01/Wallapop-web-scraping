import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline


# Modelo IA
class ModelHandler:
    def __init__(self, model_name: str, local_model_path: str):
        self.model_name = model_name
        self.local_model_path = local_model_path
        self.tokenizer = None
        self.model = None
        self.text_classifier = None
        self._load_or_download_model()

    def _load_or_download_model(self):
        if not os.path.exists(self.local_model_path):
            print("Modelo no encontrado localmente. Descargando...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.tokenizer.save_pretrained(self.local_model_path)
            self.model.save_pretrained(self.local_model_path)
        else:
            print("Modelo encontrado localmente. Cargando...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.local_model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.local_model_path)
        self.text_classifier = pipeline('text-classification', model=self.model, tokenizer=self.tokenizer)

    def classify_product(self, name: str, description: str, product_query: str) -> bool:
        # Create a clear and structured prompt in English
        prompt = (
            f"User query: {product_query}\n\n"
            f"Product title: {name}\n\n"
            f"Product description: {description}\n\n"
            "Does this product match the user's query? Respond with 'LABEL_1' if relevant or 'LABEL_0' if not."
        )
        
        result = self.text_classifier(prompt)
        return result[0]['label'] == 'LABEL_1'

