namespace Arcanis.AI.StateMachine;

/// <summary>
/// Represents the status of a state.
/// </summary>
public enum StateStatus
{
    /// <summary>The state is not active.</summary>
    Inactive,
    /// <summary>The state is entering.</summary>
    Entering,
    /// <summary>The state is active and running.</summary>
    Running,
    /// <summary>The state is exiting.</summary>
    Exiting
}

/// <summary>
/// Represents a transition condition between states.
/// </summary>
/// <param name="context">The state machine context.</param>
/// <returns>True if the transition should occur; otherwise, false.</returns>
public delegate bool TransitionCondition<TContext>(TContext context);

/// <summary>
/// Represents a state in the state machine.
/// </summary>
/// <typeparam name="TContext">The type of context passed to states.</typeparam>
public interface IState<TContext>
{
    /// <summary>Gets the name of the state.</summary>
    string Name { get; }

    /// <summary>Gets or sets the current status of the state.</summary>
    StateStatus Status { get; set; }

    /// <summary>Called when entering the state.</summary>
    Task EnterAsync(TContext context);

    /// <summary>Called during the state's update loop.</summary>
    Task UpdateAsync(TContext context);

    /// <summary>Called when exiting the state.</summary>
    Task ExitAsync(TContext context);
}

/// <summary>
/// Represents a transition between states.
/// </summary>
/// <typeparam name="TContext">The type of context.</typeparam>
public class Transition<TContext>
{
    /// <summary>The target state name.</summary>
    public string TargetState { get; set; } = string.Empty;

    /// <summary>The condition that triggers this transition.</summary>
    public TransitionCondition<TContext>? Condition { get; set; }

    /// <summary>Priority of this transition (higher = checked first).</summary>
    public int Priority { get; set; }
}

/// <summary>
/// A finite state machine implementation with async support.
/// Supports hierarchical states, transitions, and state history.
/// </summary>
/// <typeparam name="TContext">The type of context passed to states.</typeparam>
public class StateMachine<TContext>
{
    private readonly Dictionary<string, IState<TContext>> _states;
    private readonly Dictionary<string, List<Transition<TContext>>> _transitions;
    private IState<TContext>? _currentState;
    private IState<TContext>? _previousState;
    private readonly Stack<string> _stateHistory;

    /// <summary>
    /// Gets the current state.
    /// </summary>
    public IState<TContext>? CurrentState => _currentState;

    /// <summary>
    /// Gets the previous state.
    /// </summary>
    public IState<TContext>? PreviousState => _previousState;

    /// <summary>
    /// Gets whether the state machine has a current state.
    /// </summary>
    public bool HasCurrentState => _currentState != null;

    /// <summary>
    /// Gets the state history.
    /// </summary>
    public IReadOnlyCollection<string> StateHistory => _stateHistory;

    /// <summary>Event fired when the state changes.</summary>
    public event EventHandler<StateChangedEventArgs<TContext>>? StateChanged;

    /// <summary>
    /// Initializes a new StateMachine.
    /// </summary>
    public StateMachine()
    {
        _states = new Dictionary<string, IState<TContext>>();
        _transitions = new Dictionary<string, List<Transition<TContext>>>();
        _stateHistory = new Stack<string>();
    }

    /// <summary>
    /// Adds a state to the state machine.
    /// </summary>
    /// <param name="state">The state to add.</param>
    public void AddState(IState<TContext> state)
    {
        _states[state.Name] = state;
        _transitions[state.Name] = new List<Transition<TContext>>();
    }

    /// <summary>
    /// Adds a transition between states.
    /// </summary>
    /// <param name="fromState">The source state name.</param>
    /// <param name="toState">The target state name.</param>
    /// <param name="condition">The transition condition.</param>
    /// <param name="priority">Transition priority.</param>
    public void AddTransition(string fromState, string toState, TransitionCondition<TContext> condition, int priority = 0)
    {
        if (!_transitions.ContainsKey(fromState))
            throw new ArgumentException($"State '{fromState}' not found.", nameof(fromState));

        _transitions[fromState].Add(new Transition<TContext>
        {
            TargetState = toState,
            Condition = condition,
            Priority = priority
        });

        _transitions[fromState].Sort((a, b) => b.Priority.CompareTo(a.Priority));
    }

    /// <summary>
    /// Sets the initial state.
    /// </summary>
    /// <param name="stateName">The name of the initial state.</param>
    /// <param name="context">The context.</param>
    public async Task SetInitialStateAsync(string stateName, TContext context)
    {
        if (!_states.TryGetValue(stateName, out var state))
            throw new ArgumentException($"State '{stateName}' not found.", nameof(stateName));

        _currentState = state;
        await _currentState.EnterAsync(context);
        _currentState.Status = StateStatus.Running;
    }

    /// <summary>
    /// Updates the state machine.
    /// </summary>
    /// <param name="context">The context.</param>
    public async Task UpdateAsync(TContext context)
    {
        if (_currentState == null) return;

        // Check for transitions
        if (_transitions.TryGetValue(_currentState.Name, out var transitions))
        {
            foreach (var transition in transitions)
            {
                if (transition.Condition?.Invoke(context) == true)
                {
                    await TransitionToAsync(transition.TargetState, context);
                    return;
                }
            }
        }

        // Update current state
        await _currentState.UpdateAsync(context);
    }

    /// <summary>
    /// Forces a transition to a specific state.
    /// </summary>
    /// <param name="stateName">The target state name.</param>
    /// <param name="context">The context.</param>
    public async Task TransitionToAsync(string stateName, TContext context)
    {
        if (!_states.TryGetValue(stateName, out var newState))
            throw new ArgumentException($"State '{stateName}' not found.", nameof(stateName));

        if (_currentState != null)
        {
            _currentState.Status = StateStatus.Exiting;
            await _currentState.ExitAsync(context);
            _currentState.Status = StateStatus.Inactive;
            _previousState = _currentState;
        }

        _stateHistory.Push(stateName);

        _currentState = newState;
        _currentState.Status = StateStatus.Entering;
        await _currentState.EnterAsync(context);
        _currentState.Status = StateStatus.Running;

        StateChanged?.Invoke(this, new StateChangedEventArgs<TContext>
        {
            PreviousState = _previousState,
            CurrentState = _currentState,
            Context = context
        });
    }

    /// <summary>
    /// Checks if a transition is possible from the current state.
    /// </summary>
    /// <param name="targetState">The target state name.</param>
    /// <param name="context">The context.</param>
    /// <returns>True if the transition is possible; otherwise, false.</returns>
    public bool CanTransitionTo(string targetState, TContext context)
    {
        if (_currentState == null) return false;

        if (_transitions.TryGetValue(_currentState.Name, out var transitions))
        {
            return transitions.Any(t => t.TargetState == targetState && t.Condition?.Invoke(context) == true);
        }

        return false;
    }

    /// <summary>
    /// Gets a state by name.
    /// </summary>
    /// <param name="stateName">The state name.</param>
    /// <returns>The state if found; otherwise, null.</returns>
    public IState<TContext>? GetState(string stateName)
    {
        return _states.TryGetValue(stateName, out var state) ? state : null;
    }
}

/// <summary>
/// Event args for state changes.
/// </summary>
public class StateChangedEventArgs<TContext> : EventArgs
{
    /// <summary>The previous state.</summary>
    public IState<TContext>? PreviousState { get; set; }
    /// <summary>The current state.</summary>
    public IState<TContext>? CurrentState { get; set; }
    /// <summary>The context.</summary>
    public TContext? Context { get; set; }
}
