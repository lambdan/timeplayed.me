export interface DiscordUserInfo {
  id: string;
  username: string;
  avatarURL: string;
  fetchedAt: number;
  bannerColor: string;
  /*
    {
  id: '84733730387673088',
  username: 'djs',
  avatar: '3a313d57b0a1e98f8a797aa621db8a2e',
  discriminator: '0',
  public_flags: 0,
  flags: 0,
  banner: null,
  accent_color: 8585376,
  global_name: 'djs',
  avatar_decoration_data: null,
  banner_color: '#8300a0',
  clan: null,
  primary_guild: null
}*/
}

const CACHE_EXPIRE = 1 * 60 * 60 * 1000; // 1 hour

export class Discord {
  private token: string;
  private cache = new Map<string, DiscordUserInfo>();

  constructor(token: string) {
    this.token = token;
    if (!this.token) {
      throw new Error("No discord token?");
    }
  }

  async getUser(userID: string): Promise<DiscordUserInfo | null> {
    if (this.cache.has(userID)) {
      const cached = this.cache.get(userID)!;
      const age = Date.now() - cached.fetchedAt;
      if (age < CACHE_EXPIRE) {
        //console.log("Using cached discord info :D");
        return cached;
      }
    }
    //console.warn("Going out to discord!");
    const response = await fetch(`https://discord.com/api/v9/users/${userID}`, {
      headers: {
        Authorization: `Bot ${this.token}`,
      },
    });
    if (!response.ok) throw new Error(`Error status code: ${response.status}`);
    const parsed = await response.json();
    if (parsed) {
      const data: DiscordUserInfo = {
        fetchedAt: Date.now(),
        id: parsed.id,
        username: parsed.username,
        avatarURL: `https://cdn.discordapp.com/avatars/${userID}/${parsed.avatar}`,
        bannerColor: parsed.banner_color
      };
      this.cache.set(userID, data);
      return data;
    }
    return null;
  }
}
