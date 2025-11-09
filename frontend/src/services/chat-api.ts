const CHAT_BAST_URL = "/code_chat/api";

export const chatApi = {
    
    sendMessage: async (
        sessionId: string, 
        query: string, 
        conversationId: string,
        onEvent?: (event: string, data: any) => void
    ) => {
        const response = await fetch(`${CHAT_BAST_URL}/chat/${sessionId}`, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                conversation_id: conversationId
            })
        });

        if (!response.body) {
            throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                
                // 保留最后一个不完整的行
                buffer = lines.pop() || '';
                
                let currentEvent = 'text_delta';
                for (const line of lines) {
                    console.log("line", line);
                    if (line.startsWith('event: ')) {
                        currentEvent = line.slice(7).trim();
                    } else if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim();
                        console.log("dataStr", dataStr);
                        try {
                            const data = JSON.parse(dataStr);
                            console.log('Parsed SSE data:', data);
                            console.log("currentEvent", currentEvent);
                            if (onEvent && currentEvent) {
                                onEvent(currentEvent, data);
                            }
                        } catch (e) {
                            console.log('Failed to parse SSE data:', e);
                            console.error('Failed to parse SSE data:', dataStr, e);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }
}