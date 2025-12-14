export interface SGDBGrid {
  id: number;
  score: number;
  width: number;
  height: number;
  style: string;
  mime: string;
  language: string;
  url: string;
  thumbnail: string;
  type: string;
  author: {
    name: string;
    steam64: string;
    avatar: string;
  };
}

export interface SGDBGame {
  id: number;
  name: string;
  //types: ["steam", "gog", "origin"];
  verified: boolean;
  /**
   * "2015-05-19T00:00:00"
   */
  release_date: string | undefined;
}