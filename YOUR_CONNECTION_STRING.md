# Your MongoDB Connection String

## ✅ Connection String Configured

Your MongoDB connection string has been set up in `upload_images_to_mongodb.py`.

**Your Connection Details:**
- **Username:** `i211707_db_user`
- **Password:** `2103921`
- **Cluster:** `cluster0.124kx3o.mongodb.net`
- **Database:** `wearsmart`
- **Collection:** `clothing_images`

---

## 🚀 Quick Start

### Option 1: Run the Upload Script Directly
```bash
python upload_images_to_mongodb.py
```

### Option 2: Test Connection First
```bash
python setup_mongodb.py
```

---

## 🔧 Connection String Format

Your connection string is:
```
mongodb+srv://i211707_db_user:2103921@cluster0.124kx3o.mongodb.net/wearsmart?retryWrites=true&w=majority
```

**Note:** Since your password doesn't contain special characters, no URL encoding is needed.

---

## ⚠️ Important Security Notes

1. **Never commit this file to Git** - The connection string contains your password
2. **Add to .gitignore:**
   ```
   upload_images_to_mongodb.py
   setup_mongodb.py
   ```

3. **For production:** Use environment variables instead:
   ```bash
   # Windows PowerShell
   $env:MONGODB_URI="mongodb+srv://i211707_db_user:2103921@cluster0.124kx3o.mongodb.net/wearsmart?retryWrites=true&w=majority"
   ```

---

## 🔍 Verify Connection

After running the script, verify in MongoDB Atlas:
1. Go to **Browse Collections**
2. Select `wearsmart` database
3. Select `clothing_images` collection
4. You should see uploaded documents!

---

## 📝 Next Steps

1. ✅ Connection string configured
2. ⏭️ Run `python upload_images_to_mongodb.py`
3. ⏭️ Verify uploads in MongoDB Atlas
4. ⏭️ Update FastAPI to use MongoDB (optional)

