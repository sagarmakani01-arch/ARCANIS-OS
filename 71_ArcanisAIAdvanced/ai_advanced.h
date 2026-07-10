/**
 * ai_advanced.h — Advanced AI Features
 *
 * LLM integration, RAG (Retrieval Augmented Generation), and AI Agents.
 */
#ifndef ARCANIS_AI_ADVANCED_H
#define ARCANIS_AI_ADVANCED_H

#include <arcanis/types.h>

#define AI_MAX_MODELS      16
#define AI_MAX_AGENTS      32
#define AI_MAX_DOCUMENTS   1024
#define AI_MAX_EMBEDDINGS  4096
#define AI_MAX_CHUNKS      8192
#define AI_MAX_NAME        64
#define AI_MAX_PROMPT      8192
#define AI_MAX_RESPONSE    16384
#define AI_MAX_TOKENS      4096
#define AI_EMBEDDING_DIM   768

typedef enum {
    MODEL_GPT2,
    MODEL_GPT3,
    MODEL_GPT4,
    MODEL_LLAMA,
    MODEL_MISTRAL,
    MODEL_CUSTOM
} model_type_t;

typedef enum {
    AGENT_TASK,
    AGENT_CONVERSATIONAL,
    AGENT_RAG,
    AGENT_MULTI_STEP,
    AGENT_REFLEXION
} agent_type_t;

typedef enum {
    TOOL_SEARCH,
    TOOL_CALC,
    TOOL_CODE,
    TOOL_FILE,
    TOOL_WEB,
    TOOL_CUSTOM
} tool_type_t;

/* ---- LLM Models ---- */

typedef struct {
    uint32_t id;
    char name[AI_MAX_NAME];
    model_type_t type;
    uint32_t max_tokens;
    uint32_t context_window;
    float temperature;
    float top_p;
    int   quantized;
    uint64_t parameters;  /* Number of parameters */
    char path[256];
    int loaded;
} llm_model_t;

typedef struct {
    uint32_t token_count;
    uint32_t tokens[AI_MAX_TOKENS];
    char text[AI_MAX_RESPONSE];
} llm_output_t;

/* ---- RAG (Retrieval Augmented Generation) ---- */

typedef struct {
    uint32_t id;
    char doc_id[64];
    char content[2048];
    char metadata[512];
    float embedding[AI_EMBEDDING_DIM];
    uint32_t chunk_index;
    uint32_t total_chunks;
} rag_document_t;

typedef struct {
    uint32_t id;
    char query[AI_MAX_PROMPT];
    uint32_t relevant_docs[32];
    uint32_t num_relevant;
    float scores[32];
} rag_query_t;

typedef struct {
    rag_document_t documents[AI_MAX_DOCUMENTS];
    uint32_t num_documents;
    uint32_t next_id;
    uint32_t embedding_model;
} rag_index_t;

/* ---- AI Agents ---- */

typedef struct {
    uint32_t id;
    char name[AI_MAX_NAME];
    tool_type_t type;
    char description[256];
    int enabled;
    uint64_t usage_count;
} agent_tool_t;

typedef struct {
    uint32_t id;
    char name[AI_MAX_NAME];
    agent_type_t type;
    uint32_t model_id;
    char system_prompt[AI_MAX_PROMPT];
    agent_tool_t tools[16];
    uint32_t num_tools;
    int      autonomous;
    uint32_t max_steps;
    uint32_t memory_size;
    char memory[8192];
    uint64_t total_tokens;
    uint64_t total_requests;
} ai_agent_t;

typedef struct {
    char role[16];      /* "system", "user", "assistant" */
    char content[4096];
} agent_message_t;

typedef struct {
    agent_message_t messages[32];
    uint32_t num_messages;
    char result[AI_MAX_RESPONSE];
    int  success;
} agent_conversation_t;

/* ---- Main AI Manager ---- */

typedef struct {
    llm_model_t models[AI_MAX_MODELS];
    uint32_t num_models;

    rag_index_t rag;
    ai_agent_t agents[AI_MAX_AGENTS];
    uint32_t num_agents;

    uint64_t total_tokens_used;
    uint64_t total_requests;
} ai_manager_t;

/* Initialize AI manager */
void ai_init(ai_manager_t* mgr);

/* ---- LLM Operations ---- */
int   ai_load_model(ai_manager_t* mgr, const char* name, model_type_t type,
                    const char* path, uint32_t max_tokens);
int   ai_unload_model(ai_manager_t* mgr, uint32_t model_id);
int   ai_generate(ai_manager_t* mgr, uint32_t model_id,
                  const char* prompt, llm_output_t* output);
int   ai_generate_stream(ai_manager_t* mgr, uint32_t model_id,
                         const char* prompt, void (*callback)(const char* chunk));
int   ai_set_temperature(ai_manager_t* mgr, uint32_t model_id, float temp);
int   ai_set_top_p(ai_manager_t* mgr, uint32_t model_id, float top_p);
int   ai_tokenize(ai_manager_t* mgr, uint32_t model_id, const char* text, uint32_t* tokens, uint32_t* count);
int   ai_detokenize(ai_manager_t* mgr, uint32_t model_id, const uint32_t* tokens, uint32_t count, char* text);

/* ---- RAG Operations ---- */
int   rag_index_document(rag_index_t* rag, const char* doc_id,
                         const char* content, const char* metadata);
int   rag_index_file(rag_index_t* rag, const char* filepath);
int   rag_query(rag_index_t* rag, const char* query, rag_query_t* result, uint32_t top_k);
int   rag_delete_document(rag_index_t* rag, const char* doc_id);
int   rag_list_documents(rag_index_t* rag, char* buf, uint32_t buf_len);
float rag_cosine_similarity(const float* a, const float* b, uint32_t dim);
int   rag_chunk_document(const char* content, uint32_t chunk_size, char chunks[][2048], uint32_t* count);

/* ---- Agent Operations ---- */
int   ai_create_agent(ai_manager_t* mgr, const char* name, agent_type_t type,
                     uint32_t model_id, const char* system_prompt);
int   ai_delete_agent(ai_manager_t* mgr, uint32_t agent_id);
int   ai_agent_chat(ai_manager_t* mgr, uint32_t agent_id,
                    const char* user_message, char* response, uint32_t response_len);
int   ai_agent_execute(ai_manager_t* mgr, uint32_t agent_id,
                       const char* task, char* result, uint32_t result_len);
int   ai_agent_add_tool(ai_manager_t* mgr, uint32_t agent_id, const agent_tool_t* tool);
int   ai_agent_remove_tool(ai_manager_t* mgr, uint32_t agent_id, uint32_t tool_id);
int   ai_list_agents(ai_manager_t* mgr, char* buf, uint32_t buf_len);
int   ai_get_agent_stats(ai_manager_t* mgr, uint32_t agent_id, char* buf, uint32_t buf_len);

/* ---- Utility ---- */
float ai_sigmoid(float x);
float ai_softmax(const float* logits, uint32_t size, uint32_t index);

#endif
