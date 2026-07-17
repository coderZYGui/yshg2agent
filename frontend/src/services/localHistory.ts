import type { ChatMessage, Conversation, RoleKey } from "../types";

const DATABASE_NAME = "privacy-compliance-review";
const DATABASE_VERSION = 1;
const CONVERSATION_STORE = "conversations";

interface StoredConversation extends Conversation {
  owner: string;
  messages: ChatMessage[];
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);

    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(CONVERSATION_STORE)) {
        database.createObjectStore(CONVERSATION_STORE, { keyPath: "id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function transactionComplete(transaction: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
    transaction.onabort = () => reject(transaction.error);
  });
}

export async function listLocalConversations(owner: string): Promise<Conversation[]> {
  const database = await openDatabase();
  try {
    const transaction = database.transaction(CONVERSATION_STORE, "readonly");
    const rows = await requestResult<StoredConversation[]>(
      transaction.objectStore(CONVERSATION_STORE).getAll()
    );
    return rows
      .filter((row) => row.owner === owner)
      .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
      .map(({ id, title, role, created_at, updated_at }) => ({
        id,
        title,
        role,
        created_at,
        updated_at,
      }));
  } finally {
    database.close();
  }
}

export async function getLocalConversation(
  owner: string,
  id: string
): Promise<StoredConversation | null> {
  const database = await openDatabase();
  try {
    const transaction = database.transaction(CONVERSATION_STORE, "readonly");
    const row = await requestResult<StoredConversation | undefined>(
      transaction.objectStore(CONVERSATION_STORE).get(id)
    );
    return row?.owner === owner ? row : null;
  } finally {
    database.close();
  }
}

export async function saveLocalConversation(
  owner: string,
  id: string,
  role: RoleKey,
  messages: ChatMessage[]
): Promise<void> {
  const existing = await getLocalConversation(owner, id);
  const now = new Date().toISOString();
  const firstQuestion = messages.find((message) => message.role === "user")?.content ?? "";
  const title = firstQuestion.replace(/\s+/g, " ").trim().slice(0, 20) || "新会话";
  const storedMessages = messages.map(({ streaming: _streaming, ...message }) => message);
  const database = await openDatabase();

  try {
    const transaction = database.transaction(CONVERSATION_STORE, "readwrite");
    transaction.objectStore(CONVERSATION_STORE).put({
      id,
      owner,
      title,
      role,
      created_at: existing?.created_at ?? now,
      updated_at: now,
      messages: storedMessages,
    } satisfies StoredConversation);
    await transactionComplete(transaction);
  } finally {
    database.close();
  }
}

export async function deleteLocalConversation(owner: string, id: string): Promise<void> {
  const existing = await getLocalConversation(owner, id);
  if (!existing) return;

  const database = await openDatabase();
  try {
    const transaction = database.transaction(CONVERSATION_STORE, "readwrite");
    transaction.objectStore(CONVERSATION_STORE).delete(id);
    await transactionComplete(transaction);
  } finally {
    database.close();
  }
}
