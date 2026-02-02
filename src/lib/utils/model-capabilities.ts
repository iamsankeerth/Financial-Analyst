import type { OpenRouterModel } from '$lib/backend/models/open-router';

export function supportsImages(model: any): boolean {
	return model?.architecture?.input_modalities?.includes('image') ?? false;
}

export function supportsReasoning(model: any): boolean {
	return model?.supported_parameters?.includes('reasoning') ?? false;
}

export function getImageSupportedModels(models: OpenRouterModel[]): OpenRouterModel[] {
	return models.filter(supportsImages);
}
