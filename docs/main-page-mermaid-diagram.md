## Диаграмма процессов для главной страницы

### Легенда цветов
- 🔵 **Синий** (loading) - операции загрузки и обработки данных
- 🟣 **Фиолетовый** (userAction) - действия пользователя и взаимодействия с интерфейсом
- 🟡 **Желтый** (apiCall) - вызовы API и сетевые запросы
- 🟢 **Зеленый** (state) - управление состоянием и сохранение данных

```mermaid
graph TB
    %% Стили для различных элементов
    classDef loading fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef userAction fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px
    classDef apiCall fill:#fffde7,stroke:#fbc02d,stroke-width:2px
    classDef state fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    
    %% Основные процессы загрузки
    MainPage["🏠 Main Page"] --> InitialLoad["⏳ Initial Load"]
    InitialLoad --> useEffect["useEffect Hook"] --> fetchQueries_Load["API Call: fetchQueries()"]
    fetchQueries_Load --> setIsLoading_True["Set isLoading = true"]
    fetchQueries_Load --> setError_Null["Set error = null"]
    fetchQueries_Load --> API_GET_Queries["GET /user-queries"]
    API_GET_Queries --> Store_Queries["Store data in queries state"]
    API_GET_Queries --> setIsLoading_False["Set isLoading = false"]
    API_GET_Queries -- "Error" --> setError["Set error state"]
    
    %% Отображение в зависимости от состояния
    setIsLoading_False --> RenderState{"Check state"}
    RenderState -- "isLoading = true" --> ShowLoadingState["Show loading spinner"]
    RenderState -- "error exists" --> ShowErrorState["Show error message"]
    RenderState -- "queries.length = 0" --> ShowEmptyState["Show empty state"]
    RenderState -- "Queries loaded" --> ShowQueryList["Show query list/grid"]
    
    %% Пользовательские действия
    MainPage --> UserActions["👤 User Actions"]
    
    %% Поиск
    UserActions --> Search["🔍 Search queries"]
    Search --> setSearchTerm["Set searchTerm state"]
    setSearchTerm --> FilterQueries["Filter queries based on search"]
    
    %% Фильтрация
    UserActions --> Filter["🔖 Filter by status"]
    Filter --> setFilterStatus["Set filterStatus state"]
    setFilterStatus --> FilterQueries
    
    %% Переключение отображения
    UserActions --> ToggleView["🔄 Switch view type"]
    ToggleView --> setViewType["Set viewType state (list/grid)"]
    
    %% Обновление списка
    UserActions --> RefreshList["🔄 Refresh queries"]
    RefreshList --> loadQueries["Call loadQueries()"]
    loadQueries --> fetchQueries_Load
    
    %% Создание нового запроса
    UserActions --> CreateQuery["➕ Create new query"]
    CreateQuery --> setIsModalOpen["Open create modal"]
    setIsModalOpen --> handleSubmit["Submit form"]
    handleSubmit --> API_POST_Query["POST /user-queries/"]
    API_POST_Query --> onQueryCreated["Update queries state"]
    API_POST_Query --> CloseModal["Close modal"]
    API_POST_Query -- "Error" --> setError_Modal["Show error in modal"]
    
    %% Переход к деталям
    UserActions --> ViewDetails["👁️ View task details"]
    ViewDetails --> handleDetailsClick["Call handleDetailsClick(taskId)"]
    handleDetailsClick --> NavigateToDetails["Navigate to /tasks/:taskId"]
    
    %% Стилизация элементов
    class InitialLoad,useEffect,fetchQueries_Load,setIsLoading_True,setIsLoading_False,setError_Null,ShowLoadingState loading
    class Search,Filter,ToggleView,RefreshList,CreateQuery,ViewDetails userAction
    class API_GET_Queries,API_POST_Query apiCall
    class RenderState,FilterQueries,Store_Queries state
```