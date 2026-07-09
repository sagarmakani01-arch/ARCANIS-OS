namespace Arcanis.DataStructures.Trees;

/// <summary>
/// A generic binary search tree implementation with O(log n) average operations.
/// Supports insertion, deletion, searching, and various traversal methods.
/// </summary>
/// <typeparam name="T">The type of elements. Must implement IComparable.</typeparam>
public class BinarySearchTree<T> where T : IComparable<T>
{
    private BinarySearchTreeNode<T>? _root;

    /// <summary>
    /// Gets the number of elements in the tree.
    /// </summary>
    public int Count { get; private set; }

    /// <summary>
    /// Gets whether the tree is empty.
    /// </summary>
    public bool IsEmpty => _root == null;

    /// <summary>
    /// Inserts a new value into the tree.
    /// </summary>
    /// <param name="value">The value to insert.</param>
    public void Insert(T value)
    {
        _root = InsertRec(_root, value);
        Count++;
    }

    private BinarySearchTreeNode<T> InsertRec(BinarySearchTreeNode<T>? node, T value)
    {
        if (node == null)
            return new BinarySearchTreeNode<T>(value);

        int comparison = value.CompareTo(node.Value);

        if (comparison < 0)
            node.Left = InsertRec(node.Left, value);
        else if (comparison > 0)
            node.Right = InsertRec(node.Right, value);

        return node;
    }

    /// <summary>
    /// Removes a value from the tree.
    /// </summary>
    /// <param name="value">The value to remove.</param>
    /// <returns>True if the value was found and removed; otherwise, false.</returns>
    public bool Remove(T value)
    {
        if (Search(value))
        {
            _root = RemoveRec(_root, value);
            Count--;
            return true;
        }
        return false;
    }

    private BinarySearchTreeNode<T>? RemoveRec(BinarySearchTreeNode<T>? node, T value)
    {
        if (node == null) return null;

        int comparison = value.CompareTo(node.Value);

        if (comparison < 0)
            node.Left = RemoveRec(node.Left, value);
        else if (comparison > 0)
            node.Right = RemoveRec(node.Right, value);
        else
        {
            if (node.Left == null) return node.Right;
            if (node.Right == null) return node.Left;

            node.Value = GetMinValue(node.Right);
            node.Right = RemoveRec(node.Right, node.Value);
        }

        return node;
    }

    private T GetMinValue(BinarySearchTreeNode<T> node)
    {
        T minValue = node.Value;
        while (node.Left != null)
        {
            minValue = node.Left.Value;
            node = node.Left;
        }
        return minValue;
    }

    /// <summary>
    /// Searches for a value in the tree.
    /// </summary>
    /// <param name="value">The value to search for.</param>
    /// <returns>True if the value exists; otherwise, false.</returns>
    public bool Search(T value)
    {
        return SearchRec(_root, value);
    }

    private bool SearchRec(BinarySearchTreeNode<T>? node, T value)
    {
        if (node == null) return false;

        int comparison = value.CompareTo(node.Value);

        if (comparison == 0) return true;
        if (comparison < 0) return SearchRec(node.Left, value);
        return SearchRec(node.Right, value);
    }

    /// <summary>
    /// Performs an in-order traversal (sorted order).
    /// </summary>
    /// <returns>An enumerable of values in sorted order.</returns>
    public IEnumerable<T> InOrderTraversal()
    {
        var result = new List<T>();
        InOrderRec(_root, result);
        return result;
    }

    private void InOrderRec(BinarySearchTreeNode<T>? node, List<T> result)
    {
        if (node == null) return;
        InOrderRec(node.Left, result);
        result.Add(node.Value);
        InOrderRec(node.Right, result);
    }

    /// <summary>
    /// Performs a pre-order traversal.
    /// </summary>
    /// <returns>An enumerable of values in pre-order.</returns>
    public IEnumerable<T> PreOrderTraversal()
    {
        var result = new List<T>();
        PreOrderRec(_root, result);
        return result;
    }

    private void PreOrderRec(BinarySearchTreeNode<T>? node, List<T> result)
    {
        if (node == null) return;
        result.Add(node.Value);
        PreOrderRec(node.Left, result);
        PreOrderRec(node.Right, result);
    }

    /// <summary>
    /// Performs a post-order traversal.
    /// </summary>
    /// <returns>An enumerable of values in post-order.</returns>
    public IEnumerable<T> PostOrderTraversal()
    {
        var result = new List<T>();
        PostOrderRec(_root, result);
        return result;
    }

    private void PostOrderRec(BinarySearchTreeNode<T>? node, List<T> result)
    {
        if (node == null) return;
        PostOrderRec(node.Left, result);
        PostOrderRec(node.Right, result);
        result.Add(node.Value);
    }

    /// <summary>
    /// Gets the minimum value in the tree.
    /// </summary>
    /// <returns>The minimum value.</returns>
    public T GetMin()
    {
        if (_root == null)
            throw new InvalidOperationException("Tree is empty.");
        return GetMinValue(_root);
    }

    /// <summary>
    /// Gets the maximum value in the tree.
    /// </summary>
    /// <returns>The maximum value.</returns>
    public T GetMax()
    {
        if (_root == null)
            throw new InvalidOperationException("Tree is empty.");

        var node = _root;
        while (node.Right != null)
            node = node.Right;
        return node.Value;
    }

    /// <summary>
    /// Clears all elements from the tree.
    /// </summary>
    public void Clear()
    {
        _root = null;
        Count = 0;
    }
}

/// <summary>
/// Represents a node in the binary search tree.
/// </summary>
public class BinarySearchTreeNode<T>
{
    /// <summary>
    /// Gets or sets the value stored in the node.
    /// </summary>
    public T Value { get; set; }

    /// <summary>
    /// Gets or sets the left child node.
    /// </summary>
    public BinarySearchTreeNode<T>? Left { get; set; }

    /// <summary>
    /// Gets or sets the right child node.
    /// </summary>
    public BinarySearchTreeNode<T>? Right { get; set; }

    /// <summary>
    /// Initializes a new instance of the BinarySearchTreeNode class.
    /// </summary>
    /// <param name="value">The value to store in the node.</param>
    public BinarySearchTreeNode(T value)
    {
        Value = value;
        Left = null;
        Right = null;
    }
}
