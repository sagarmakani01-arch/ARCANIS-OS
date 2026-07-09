using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.IdentityModel.Tokens;

namespace Arcanis.Security.Authentication;

/// <summary>
/// JWT token configuration options.
/// </summary>
public class JwtOptions
{
    /// <summary>The secret key for signing tokens.</summary>
    public string SecretKey { get; set; } = string.Empty;
    /// <summary>The issuer of the token.</summary>
    public string Issuer { get; set; } = "Arcanis";
    /// <summary>The audience for the token.</summary>
    public string Audience { get; set; } = "Arcanis";
    /// <summary>Token expiration time.</summary>
    public TimeSpan Expiration { get; set; } = TimeSpan.FromHours(1);
    /// <summary>Refresh token expiration time.</summary>
    public TimeSpan RefreshExpiration { get; set; } = TimeSpan.FromDays(7);
}

/// <summary>
/// JWT token manager for creating and validating tokens.
/// </summary>
public class JwtTokenManager
{
    private readonly JwtOptions _options;
    private readonly SigningCredentials _signingCredentials;
    private readonly JwtSecurityTokenHandler _tokenHandler;

    /// <summary>
    /// Initializes a new instance of the JwtTokenManager class.
    /// </summary>
    /// <param name="options">JWT configuration options.</param>
    public JwtTokenManager(JwtOptions options)
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));

        if (string.IsNullOrEmpty(options.SecretKey) || options.SecretKey.Length < 32)
            throw new ArgumentException("Secret key must be at least 32 characters.", nameof(options));

        var securityKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(options.SecretKey));
        _signingCredentials = new SigningCredentials(securityKey, SecurityAlgorithms.HmacSha256);
        _tokenHandler = new JwtSecurityTokenHandler();
    }

    /// <summary>
    /// Generates a JWT access token.
    /// </summary>
    /// <param name="claims">The claims to include in the token.</param>
    /// <returns>The generated token string.</returns>
    public string GenerateAccessToken(IEnumerable<Claim> claims)
    {
        var token = new JwtSecurityToken(
            issuer: _options.Issuer,
            audience: _options.Audience,
            claims: claims,
            expires: DateTime.UtcNow.Add(_options.Expiration),
            signingCredentials: _signingCredentials);

        return _tokenHandler.WriteToken(token);
    }

    /// <summary>
    /// Generates a JWT access token for a user.
    /// </summary>
    /// <param name="userId">The user ID.</param>
    /// <param name="username">The username.</param>
    /// <param name="roles">Optional roles.</param>
    /// <returns>The generated token string.</returns>
    public string GenerateAccessToken(string userId, string username, IEnumerable<string>? roles = null)
    {
        var claims = new List<Claim>
        {
            new Claim(ClaimTypes.NameIdentifier, userId),
            new Claim(ClaimTypes.Name, username),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())
        };

        if (roles != null)
        {
            foreach (var role in roles)
            {
                claims.Add(new Claim(ClaimTypes.Role, role));
            }
        }

        return GenerateAccessToken(claims);
    }

    /// <summary>
    /// Generates a refresh token.
    /// </summary>
    /// <returns>The refresh token string.</returns>
    public string GenerateRefreshToken()
    {
        var token = new JwtSecurityToken(
            issuer: _options.Issuer,
            audience: _options.Audience,
            expires: DateTime.UtcNow.Add(_options.RefreshExpiration),
            signingCredentials: _signingCredentials);

        return _tokenHandler.WriteToken(token);
    }

    /// <summary>
    /// Validates a JWT token and returns the principal.
    /// </summary>
    /// <param name="token">The token to validate.</param>
    /// <returns>The claims principal if valid; null if invalid.</returns>
    public ClaimsPrincipal? ValidateToken(string token)
    {
        var validationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = _options.Issuer,
            ValidateAudience = true,
            ValidAudience = _options.Audience,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_options.SecretKey)),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromMinutes(5)
        };

        try
        {
            var principal = _tokenHandler.ValidateToken(token, validationParameters, out _);
            return principal;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Gets the expiration date of a token.
    /// </summary>
    /// <param name="token">The token to check.</param>
    /// <returns>The expiration date if valid; null if invalid.</returns>
    public DateTime? GetTokenExpiration(string token)
    {
        try
        {
            var jwtToken = _tokenHandler.ReadJwtToken(token);
            return jwtToken.ValidTo;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Checks if a token is expired.
    /// </summary>
    /// <param name="token">The token to check.</param>
    /// <returns>True if the token is expired; otherwise, false.</returns>
    public bool IsTokenExpired(string token)
    {
        var expiration = GetTokenExpiration(token);
        return expiration.HasValue && expiration.Value < DateTime.UtcNow;
    }
}
