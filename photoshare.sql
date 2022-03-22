CREATE DATABASE IF NOT EXISTS `cs460_project` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `cs460_project`;

CREATE TABLE `Albums` (
  `album_id` int NOT NULL,
  `user_id` int NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_on` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Comments` (
  `comment_id` int NOT NULL,
  `picture_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_on` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DELIMITER $$
CREATE TRIGGER `selfComment` BEFORE INSERT ON `Comments` FOR EACH ROW BEGIN
    IF (NEW.user_id = (SELECT p.user_id FROM Pictures p WHERE p.picture_id = NEW.picture_id LIMIT 1)) THEN
    	SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'User cannot comment his/her photo';
    END IF;
END
$$
DELIMITER ;

CREATE TABLE `Friends` (
  `user_id1` int NOT NULL,
  `user_id2` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Likes` (
  `user_id` int NOT NULL,
  `picture_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Pictures` (
  `picture_id` int NOT NULL,
  `album_id` int NOT NULL,
  `user_id` int NOT NULL,
  `imgdata` longblob NOT NULL,
  `caption` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `TagPicture` (
  `picture_id` int NOT NULL,
  `tag_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Tags` (
  `tag_id` int NOT NULL,
  `tag` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `Users` (
  `user_id` int NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `date_of_birth` date NOT NULL,
  `hometown` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gender` set('Male','Female') COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


ALTER TABLE `Albums`
  ADD PRIMARY KEY (`album_id`),
  ADD KEY `user_id` (`user_id`);

ALTER TABLE `Comments`
  ADD PRIMARY KEY (`comment_id`),
  ADD KEY `picture_id` (`picture_id`),
  ADD KEY `user_id` (`user_id`);

ALTER TABLE `Friends`
  ADD UNIQUE KEY `user_id1` (`user_id1`,`user_id2`) USING BTREE,
  ADD KEY `user_id2` (`user_id2`);

ALTER TABLE `Likes`
  ADD PRIMARY KEY (`user_id`,`picture_id`),
  ADD KEY `picture_id` (`picture_id`);

ALTER TABLE `Pictures`
  ADD PRIMARY KEY (`picture_id`),
  ADD KEY `album_id` (`album_id`),
  ADD KEY `user_id` (`user_id`);

ALTER TABLE `TagPicture`
  ADD UNIQUE KEY `picture_id` (`picture_id`,`tag_id`),
  ADD KEY `tag_id` (`tag_id`);

ALTER TABLE `Tags`
  ADD PRIMARY KEY (`tag_id`),
  ADD UNIQUE KEY `UNIQUE` (`tag`);

ALTER TABLE `Users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);


ALTER TABLE `Albums`
  MODIFY `album_id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `Comments`
  MODIFY `comment_id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `Pictures`
  MODIFY `picture_id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `Tags`
  MODIFY `tag_id` int NOT NULL AUTO_INCREMENT;

ALTER TABLE `Users`
  MODIFY `user_id` int NOT NULL AUTO_INCREMENT;


ALTER TABLE `Albums`
  ADD CONSTRAINT `Albums_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE;

ALTER TABLE `Comments`
  ADD CONSTRAINT `Comments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `Comments_ibfk_2` FOREIGN KEY (`picture_id`) REFERENCES `Pictures` (`picture_id`) ON DELETE CASCADE;

ALTER TABLE `Friends`
  ADD CONSTRAINT `Friends_ibfk_1` FOREIGN KEY (`user_id1`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `Friends_ibfk_2` FOREIGN KEY (`user_id2`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE;

ALTER TABLE `Likes`
  ADD CONSTRAINT `Likes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `Likes_ibfk_2` FOREIGN KEY (`picture_id`) REFERENCES `Pictures` (`picture_id`) ON DELETE CASCADE;

ALTER TABLE `Pictures`
  ADD CONSTRAINT `Pictures_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `Pictures_ibfk_2` FOREIGN KEY (`album_id`) REFERENCES `Albums` (`album_id`) ON DELETE CASCADE;

ALTER TABLE `TagPicture`
  ADD CONSTRAINT `TagPicture_ibfk_1` FOREIGN KEY (`tag_id`) REFERENCES `Tags` (`tag_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `TagPicture_ibfk_2` FOREIGN KEY (`picture_id`) REFERENCES `Pictures` (`picture_id`) ON DELETE CASCADE;
COMMIT;
