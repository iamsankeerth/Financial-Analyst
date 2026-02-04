/**
 * Client-side function to call the stock analysis API
 */
import { err, ok, Result, ResultAsync } from 'neverthrow';

interface StockAnalyzeRequest {
    message: string;
    session_token: string;
    conversation_id?: string;
    skip_user_message?: boolean;
}

interface StockAnalyzeResponse {
    ok: boolean;
    conversation_id: string;
    code?: string;
    chart_base64?: string | null;
}

export async function callStockAnalyze(
    args: StockAnalyzeRequest
): Promise<Result<StockAnalyzeResponse, string>> {
    const response = await ResultAsync.fromPromise(
        fetch('/api/stock-analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(args),
        }),
        (e) => `Network error: ${e}`
    );

    if (response.isErr()) {
        return err(response.error);
    }

    const res = response.value;

    if (!res.ok) {
        const errorText = await res.text().catch(() => 'Unknown error');
        return err(errorText);
    }

    const data = await ResultAsync.fromPromise(
        res.json() as Promise<StockAnalyzeResponse>,
        (e) => `Failed to parse response: ${e}`
    );

    if (data.isErr()) {
        return err(data.error);
    }

    return ok(data.value);
}
