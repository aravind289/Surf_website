from sentence_transformers import SentenceTransformer
import numpy as np

class SentenceTransformerEmbeddingFunction:
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)
    
    def __call__(self, input):
        """
        Generate embeddings for the given input using SentenceTransformer.
        
        Args:
            input: A string or list of strings to generate embeddings for.
            
        Returns:
            A list of embeddings, each embedding is a list of floats.
        """
        if isinstance(input, str):
            input = [input]
        embeddings = self.model.encode(input, convert_to_tensor=True)
        return embeddings.cpu().numpy().tolist()
    
    def to(self, device):
        """Move the model to the specified device (e.g., 'cuda')."""
        self.model = self.model.to(device)
        return self
