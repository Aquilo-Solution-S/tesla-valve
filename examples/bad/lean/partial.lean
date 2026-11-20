-- expect: retry is partial or opaque
partial def retry (attempt : Nat) : Nat := retry (attempt + 1)
