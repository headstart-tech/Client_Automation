"""
Templete gallery related functions
"""
from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.dependencies.oauth import cache_invalidation
from bson import ObjectId
from app.core.custom_error import CustomError

class TemplateGallery:
    """
    Functions related to template gallery
    """ 

    async def media_uploaded_user_helper(self) -> list[dict]:
        """Helper funciton for getting users list which has uploaded media on template media gallery

        Returns:
            list: List of users with user name and unique id
        """
        user_list = await DatabaseConfiguration().template_gallery.aggregate([{
            '$group': {
                '_id': '$uploaded_by'
            }
        }, {
            '$project': {
                '_id': 0, 
                'uploaded_by': '$_id'
            }
        }]).to_list(None)

        users = []
        for user in user_list:
            username = user.get("uploaded_by")
            user_details = await DatabaseConfiguration().user_collection.find_one({"user_name": username})
            if user_details:
                data = {
                    "id": str(user_details.get("_id")),
                    "user_name": username,
                    "name": utility_obj.name_can(user_details)
                }
                users.append(data)
                
        return users
    
    
    async def template_gallery_delete_helper(self, data_ids: list[str]) -> dict:
        """Helper function for deleting the media data from the db

        Params:
            data_ids (list[str]): list of media id which has to be deleted

        Returns:
            dict: Response message.
        """

        object_ids = [ObjectId(data_id) for data_id in data_ids]

        await DatabaseConfiguration().template_gallery.update_many(
            {"_id": {"$in": object_ids}},  # Match documents where _id is in the list of object_ids
            {"$set": {"is_deleted": True}}  # Set the is_deleted field to True
        )

        await cache_invalidation(api_updated="templates/delete_gallery_data")

        return {"message": "Gallery data deleted successfully!!"}


    async def template_gallery_download_helper(self, object_ids: list[str]) -> list:
        """Helper function of template media gallery download links

        Params:
            object_ids (list[str]): Unique id list of media which has to be download

        Returns:
            list: List of public url links which has to be download.
        """
        
        media_list = await DatabaseConfiguration().template_gallery.aggregate([
            {
                "$match": {
                    "_id": {
                        "$in": object_ids
                    },
                    "is_deleted": False,
                    "media_url": {
                        "$ne": None 
                    }
                }
            }, {
                "$group": {
                    "_id": None,
                    "media_links": {
                        "$addToSet": "$media_url"
                    }
                }
            }, {
                "$project": {
                    "_id": 0,
                    "media_links": 1
                }
            }
        ]).to_list(None)

        return media_list[0] if media_list else []


    async def template_gallery_data_helper(self, media_type: list[str]|None = None, uploaded_by: list[str]|None = None, date_range: dict|None = None, search: str|None = None, page_num: int|None = None, page_size: int|None = None) -> list:
        """\nHelper function for getting template gallery data with filter.

        Params:\n
            media_type (list[str] | None, optional): It it for filtering file_type data. Defaults to None.
            uploaded_by (list[str] | None, optional): Uploaded user filteration. Defaults to None.
            date_range (dict | None, optional): Date range filter according to start and end date. Defaults to None.
            search (str | None, optional): search query data filteration. Defaults to None.
            page_num (int | None, optional): Current page no.. Defaults to None.
            page_size (int | None, optional): Data limit in per page. Default to None.
            
        Returns:\n
            list: List of data of uploaded medias
        """
        skip, limit = await utility_obj.return_skip_and_limit(page_num, page_size)
        base_match = {
            "is_deleted": False
        }

        if date_range:
            start_date, end_date = await utility_obj.date_change_format(
                date_range.get('start_date'),
                date_range.get('end_date'))
            base_match.update({
                "uploaded_on": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })

        if uploaded_by:
            base_match.update({
                "uploaded_by": {
                    "$in": uploaded_by
                }
            })

        if media_type:
            base_match.update({
                "file_type": {
                    "$in": media_type
                }
            })

        if search:
            base_match.update({
                "file_name": {
                    "$regex": search,
                    "$options": "i"
                }
            })

        galleries = await (DatabaseConfiguration().template_gallery.aggregate([{
            "$match": base_match
        }, {
            "$facet": {
                "paginated_results": [{"$skip": skip}, {"$limit": limit}],
                "totalCount": [{"$count": "count"}]
            }
        }])).to_list(None)

        data = []
        galleries = galleries[0] if galleries else {}
        galleries, count = galleries.get("paginated_results", []), galleries.get("totalCount", [])[0].get("count", 0) if galleries.get("totalCount") else 0


        for gallery in galleries:
            gallery.pop("is_deleted", None)
            gallery.update({
                "id": str(gallery.pop("_id")),
                "uploaded_on": utility_obj.get_local_time(gallery.pop("uploaded_on")) if gallery.get("uploaded_on") else None,
            })
            data.append(gallery)

        return data, count
    

    async def template_gallery_spec_media_helper(self, media_id: str) -> dict:
        """Helper function of getting all details of specifc gallery media

        Params:
            media_id (str): Unique media id

        Raises:
            CustomError: Raise if passes invalid media id

        Returns:
            dict: All details of media in dictionary.
        """
        media = await DatabaseConfiguration().template_gallery.find_one({
            "_id": ObjectId(media_id),
            "is_deleted": False
        })

        if media:
            media.pop("is_deleted")
            media.update({
                "id": str(media.pop("_id")),
                "uploaded_on": utility_obj.get_local_time(media.get("uploaded_on")) if media.get("uploaded_on") else None,
                "file_size": utility_obj.format_float_to_2_places(media.get("file_size"))
            })

            return media
        
        else:
            raise CustomError("Invalid media ID")