export const fetchSearch = async (query: string, filters = {}) => {
  const params = new URLSearchParams({ q: query, ...filters });
  const res = await fetch(`http://localhost:8000/search?${params}`);
  return res.json();
};

export const fetchConversation = async (convId: string) => {
  const res = await fetch(`http://localhost:8000/conversation/${convId}/timeline`);
  return res.json();
};

export const buildContextPack = async (messageIds: string[], maxTokens: number) => {
  const res = await fetch('http://localhost:8000/context/pack', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message_ids: messageIds, max_tokens: maxTokens })
  });
  return res.json();
};