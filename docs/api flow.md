# API Flow

1. User write a query. Example: "how to internet is working?" POST http://localhost:8000/user-queries/
2. API get the query and save it in database as UserQueryDB {id: "123", "task_id": "123", "origin_query": "how to internet is working?"} and return to user.
3. User get the response and see the task_id.
4. Next step is to clarify context. Call POST http://localhost:8000/tasks/{task_id}/clarify_context with empty user_interaction and getting ContextSufficiencyResult. {"is_context_sufficient": True, "follow_up_question": "What aspects of the internet are you interested in?"}. 
5. user answer to the question and call the same endpoint POST http://localhost:8000/tasks/{task_id}/clarify_context with new user_interaction. UserInteraction {"query": "What aspects of the internet are you interested in?", "answer": "I want to know how the internet works."}
6. API save the user_interaction to task and call clarify_context again with new user_interaction.
7. This process (point 4-6) will be repeated few times until is_context_sufficient will be True. And user get in response {"is_context_sufficient": True}.
8. Next step is to analyze the task. Call POST http://localhost:8000/tasks/{task_id}/analyze
9. API save the analysis to the database and return to user AnalysisResult
10. Next step is to generate concepts. Call POST http://localhost:8000/tasks/{task_id}/generate-concepts
11. API save the concepts to the database and return to user ConceptsResult