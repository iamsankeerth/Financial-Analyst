/**
 * Stock Analysis API Endpoint
 * Calls our Python backend for Gemini-powered stock analysis
 */
import { PUBLIC_CONVEX_URL } from '$env/static/public';
import { api } from '$lib/backend/convex/_generated/api';
import type { Id } from '$lib/backend/convex/_generated/dataModel';
import { Provider } from '$lib/types';
import { error, json, type RequestHandler } from '@sveltejs/kit';
import { getSessionCookie } from 'better-auth/cookies';
import { ConvexHttpClient } from 'convex/browser';
import { ResultAsync } from 'neverthrow';
import { z } from 'zod/v4';

const PYTHON_API_URL = 'http://localhost:8000';

const reqBodySchema = z.object({
    message: z.string(),
    session_token: z.string(),
    conversation_id: z.string().optional(),
    skip_user_message: z.boolean().optional(),
});

const client = new ConvexHttpClient(PUBLIC_CONVEX_URL);

export const POST: RequestHandler = async ({ request }) => {
    const startTime = Date.now();
    console.log('[StockAnalyze] Starting request');

    // Parse request body
    const bodyResult = await ResultAsync.fromPromise(
        request.json(),
        () => 'Failed to parse request body'
    );

    if (bodyResult.isErr()) {
        return error(400, 'Failed to parse request body');
    }

    const parsed = reqBodySchema.safeParse(bodyResult.value);
    if (!parsed.success) {
        return error(400, parsed.error.toString());
    }
    const args = parsed.data;

    // Get session from cookie (use test token for development)
    const cookie = getSessionCookie(request.headers);
    const sessionToken = cookie?.split('.')[0] ?? 'test-token';

    // Auth bypassed for testing

    let conversationId = args.conversation_id;

    // Create new conversation if needed
    if (!conversationId) {
        const convResult = await ResultAsync.fromPromise(
            client.mutation(api.conversations.createAndAddMessage, {
                content: args.message,
                content_html: '',
                role: 'user',
                session_token: sessionToken,
            }),
            (e) => `Failed to create conversation: ${e}`
        );

        if (convResult.isErr()) {
            return error(500, 'Failed to create conversation');
        }

        conversationId = convResult.value.conversationId;

        // Set title to match query
        await client.mutation(api.conversations.updateTitle, {
            conversation_id: conversationId as Id<'conversations'>,
            title: args.message.slice(0, 50),
            session_token: sessionToken,
        });
    } else if (!args.skip_user_message) {
        // Add user message to existing conversation if not skipped
        await client.mutation(api.messages.create, {
            conversation_id: conversationId,
            content: args.message,
            session_token: sessionToken,
            role: 'user',
        });
    }

    // Set generating status
    await client.mutation(api.conversations.updateGenerating, {
        conversation_id: conversationId as Id<'conversations'>,
        generating: true,
        session_token: sessionToken,
    });

    // Call Python API
    try {
        const pythonResponse = await fetch(`${PYTHON_API_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: args.message,
                chat_id: conversationId,
            }),
        });

        if (!pythonResponse.ok) {
            throw new Error(`Python API error: ${pythonResponse.statusText}`);
        }

        const result = await pythonResponse.json();

        // Parse result.code to separate Python code from # Output comments
        let pythonCode = result.code;
        let printedOutput = '';

        if (pythonCode.includes('# Output:')) {
            const parts = pythonCode.split('# Output:');
            pythonCode = parts[0].trim();
            printedOutput = parts[1].trim();
            // Remove leading # from outputs
            printedOutput = printedOutput.split('\n').map((line: string) => line.replace(/^#\s?/, '')).join('\n');
        } else if (pythonCode.includes('# Error executing:')) {
            // Handle error cases gracefully
            const parts = pythonCode.split('# Error executing:');
            // Maintain the full content for markdown, but extract for HTML
        }

        // Build Markdown content for the main UI
        let markdownContent = '```python\n' + pythonCode + '\n```';
        if (printedOutput) {
            markdownContent += '\n\n**Analysis Output:**\n```text\n' + printedOutput + '\n```';
        }
        if (result.chart_base64) {
            markdownContent += `\n\n![Stock Chart](data:image/png;base64,${result.chart_base64})`;
        }

        // Build HTML content for optimized rendering
        let htmlContent = `<div class="analysis-result">
            <details>
                <summary>Analysis Code</summary>
                <pre><code class="language-python">${pythonCode}</code></pre>
            </details>`;

        if (printedOutput) {
            htmlContent += `<div class="output-log">
                <span class="label">Execution Output</span>
                <pre class="whitespace-pre-wrap">${printedOutput}</pre>
            </div>`;
        }

        if (result.chart_base64) {
            htmlContent += `<div class="chart-container mt-4">
                <img src="data:image/png;base64,${result.chart_base64}" alt="Stock Chart" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);" />
            </div>`;
        }
        htmlContent += `</div>`;

        // Add assistant message to Convex
        await client.mutation(api.messages.create, {
            conversation_id: conversationId,
            content: markdownContent,
            content_html: htmlContent,
            role: 'assistant',
            session_token: sessionToken,
            model_id: 'financial-analyst',
            provider: Provider.OpenRouter,
        });

        // Reset generating status
        await client.mutation(api.conversations.updateGenerating, {
            conversation_id: conversationId as Id<'conversations'>,
            generating: false,
            session_token: sessionToken,
        });

        console.log(`[StockAnalyze] Completed in ${Date.now() - startTime}ms`);

        return json({
            ok: true,
            conversation_id: conversationId,
            code: result.code,
            chart_base64: result.chart_base64,
        });
    } catch (e) {
        console.error('[StockAnalyze] Error:', e);

        // Reset generating status
        await client.mutation(api.conversations.updateGenerating, {
            conversation_id: conversationId as Id<'conversations'>,
            generating: false,
            session_token: sessionToken,
        });

        // Add error message
        await client.mutation(api.messages.create, {
            conversation_id: conversationId,
            content: `Error analyzing stock: ${e instanceof Error ? e.message : 'Unknown error'}`,
            role: 'assistant',
            session_token: sessionToken,
        });

        return error(500, 'Stock analysis failed');
    }
};
