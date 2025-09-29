import open_clip
import torch
import torchvision.models as models
from torchvision.transforms import Compose, Resize, CenterCrop, ToTensor, Normalize
from torchvision.models import ResNet50_Weights
from PIL import Image
from typing import Optional


class ClipModel:
    MODEL: str = 'ViT-B-32'
    PRETRAINED_ON: str = 'laion2b_s34b_b79k'
    FEATURE_PATH: str = 'features/clip_features.pt'
    DEVICE: str = 'cuda' if torch.cuda.is_available() else 'cpu'

    def __init__(self):
        self.clip_model, _, _ = open_clip.create_model_and_transforms(
            self.MODEL,
            pretrained=self.PRETRAINED_ON,
            device=self.DEVICE
        )
        self.clip_model.eval()
        self.tokenizer = open_clip.get_tokenizer(self.MODEL)
        self.clip_features = torch.load(self.FEATURE_PATH, map_location=self.DEVICE)

        self.resnet = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1).to(self.DEVICE)
        self.resnet.eval()
        self.resnet_transform = Compose([
            Resize(256),
            CenterCrop(224),
            ToTensor(),
            Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def similarity(self, index: int) -> torch.Tensor:
        target_features = self.clip_features[index]

        similarities = target_features @ self.clip_features.T

        sorted_indices = similarities.argsort(descending=True)
        return sorted_indices[sorted_indices != index]

    def search(self, text: str, video_filter: Optional[str] = None) -> torch.Tensor:
        query = self.tokenizer(text).to(self.DEVICE)
        with torch.no_grad():
            text_features = self.clip_model.encode_text(query).squeeze()
            text_features /= text_features.norm()

        similarities = text_features @ self.clip_features.T
        indices = similarities.argsort(descending=True)

        if video_filter:
            indices = self._filter_by_video(indices, video_filter)

        top_k = 50
        if len(indices) > 0:
            reranked = self._resnet_rerank(indices[:top_k])
            final_indices = torch.cat([reranked, indices[top_k:]])
        else:
            final_indices = indices

        return final_indices.cpu()

    def _resnet_rerank(self, indices: torch.Tensor) -> torch.Tensor:
        from image_handler import ImageHandler
        images = ImageHandler()

        resnet_features = []
        for idx in indices:
            img = Image.open(images[idx])
            img_t = self.resnet_transform(img).unsqueeze(0).to(self.DEVICE)
            with torch.no_grad():
                features = self.resnet(img_t).squeeze()
                features /= features.norm()
            resnet_features.append(features)

        resnet_features = torch.stack(resnet_features)

        top1_resnet = resnet_features[0].unsqueeze(0)
        resnet_sim = top1_resnet @ resnet_features.T
        resnet_sim = resnet_sim.squeeze()

        return indices[resnet_sim.argsort(descending=True)]

    def _filter_by_video(self, indices: torch.Tensor, video_name: str) -> torch.Tensor:
        from image_handler import ImageHandler
        images = ImageHandler()
        filtered = []
        for idx in indices:
            path = images[idx]
            current_video = path.split('/')[-2]
            if current_video == video_name:
                filtered.append(idx)
        return torch.tensor(filtered, device=self.DEVICE) if filtered else indices