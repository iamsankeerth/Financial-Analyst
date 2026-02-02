import { Provider } from '$lib/types';

export interface StaticModel {
	id: string;
	name: string;
	description: string;
}

export type ProviderModelMap = {
	[Provider.OpenRouter]: StaticModel;
	[Provider.HuggingFace]: never;
	[Provider.OpenAI]: never;
	[Provider.Anthropic]: never;
};
